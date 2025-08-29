"""Client for fetching planning (Taba) data from land.gov.il.

This class wraps the ``TabaSearch`` API endpoint and exposes a ``fetch_plans``
method that paginates through results and returns them as a
:class:`pandas.DataFrame`.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import pandas as pd
import requests


class RamiClient:
    """Simple client for the RAMI TabaSearch API."""

    ENDPOINT = "https://apps.land.gov.il/TabaSearch/api//SerachPlans/GetPlans"
    BASE_URL = "https://apps.land.gov.il"

    DEFAULT_HEADERS: Dict[str, str] = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "he,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    def __init__(
        self,
        *,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        page_param: str = "page",
        size_param: str = "size",
        page_size: int = 100,
        max_pages: int = 200,
        delay: float = 0.2,
        session: Optional[requests.Session] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        self.session = session or requests.Session()
        self.headers = dict(self.DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.cookies = cookies
        self.page_param = page_param
        self.size_param = size_param
        self.page_size = page_size
        self.max_pages = max_pages
        self.delay = delay
        self.endpoint = endpoint or self.ENDPOINT
        # Ensure a User-Agent header exists on the session for some picky APIs
        self.session.headers.update({"User-Agent": self.headers.get("User-Agent", "Mozilla/5.0")})

    def _one_page(self, search_params: Dict[str, Any], page: int) -> Dict[str, Any]:
        """Fetch a single page of search results."""
        payload = dict(search_params)
        if self.page_param:
            payload[self.page_param] = page
        if self.size_param:
            payload[self.size_param] = self.page_size
        response = self.session.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            cookies=self.cookies,
            timeout=60,
        )
        if response.status_code == 401:
            raise RuntimeError("401 Unauthorized – missing Cookie/Authorization headers?")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _extract_results(data: Any) -> Iterable[Any]:
        """Return the list of items from a response payload."""
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        # Check for RAMI API specific format first
        if "plansSmall" in data and isinstance(data["plansSmall"], list):
            return data["plansSmall"]
        # Fallback to generic field names
        for key in ("data", "result", "results", "items"):
            node = data.get(key) if isinstance(data, dict) else None
            if isinstance(node, list):
                return node
            if isinstance(node, dict) and "items" in node:
                return node["items"]
        return []

    @staticmethod
    def _extract_total(data: Any) -> Optional[int]:
        """Attempt to extract total count of records from response payload."""
        if not isinstance(data, dict):
            return None
        # Check for RAMI API specific format first
        if "totalRecords" in data and isinstance(data["totalRecords"], int):
            return data["totalRecords"]
        # Fallback to generic field names
        for key in ("total", "count", "TotalCount"):
            value = data.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, dict) and isinstance(value.get("value"), int):
                return value["value"]
        return None

    def fetch_plans(self, search_params: Dict[str, Any]) -> pd.DataFrame:
        """Fetch all plan results for a given search parameters."""
        # For RAMI API, pagination doesn't work as expected
        # The API returns all results in a single request
        response = self.session.post(
            self.endpoint,
            json=search_params,  # Don't add pagination params
            headers=self.headers,
            cookies=self.cookies,
            timeout=60,
        )
        if response.status_code == 401:
            raise RuntimeError("401 Unauthorized – missing Cookie/Authorization headers?")
        response.raise_for_status()
        
        data = response.json()
        rows = list(self._extract_results(data))
        return pd.DataFrame(rows)

    def _extract_document_urls(self, plan: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract document URLs from a plan's documentsSet."""
        documents = []
        documents_set = plan.get('documentsSet', {})
        
        if not documents_set:
            return documents
        
        def clean_path(path: str) -> str:
            """Clean and normalize a file path for URL construction."""
            if not path:
                return path
            # Replace backslashes with forward slashes
            path = path.replace('\\', '/')
            # Ensure path starts with /
            if not path.startswith('/'):
                path = '/' + path
            return path
            
        # Extract takanon (regulations)
        takanon = documents_set.get('takanon')
        if takanon and takanon.get('path'):
            clean_path_str = clean_path(takanon['path'])
            documents.append({
                'type': 'takanon',
                'name': takanon.get('info', 'תקנון סרוק'),
                'url': self.BASE_URL + clean_path_str,
                'path': takanon['path']
            })
        
        # Extract tasritim (drawings/blueprints)
        tasritim = documents_set.get('tasritim', [])
        for tasrit in tasritim:
            if tasrit.get('path'):
                clean_path_str = clean_path(tasrit['path'])
                documents.append({
                    'type': 'tasrit',
                    'name': tasrit.get('info', 'תשריט'),
                    'url': self.BASE_URL + clean_path_str,
                    'path': tasrit['path']
                })
        
        # Extract nispachim (appendices)
        nispachim = documents_set.get('nispachim', [])
        for nispach in nispachim:
            if nispach.get('path'):
                clean_path_str = clean_path(nispach['path'])
                documents.append({
                    'type': 'nispach',
                    'name': nispach.get('info', 'נספח'),
                    'url': self.BASE_URL + clean_path_str,
                    'path': nispach['path']
                })
        
        # Extract MMG files
        mmg = documents_set.get('mmg')
        if mmg and mmg.get('path'):
            clean_path_str = clean_path(mmg['path'])
            documents.append({
                'type': 'mmg',
                'name': mmg.get('info', 'קבצי ממג'),
                'url': self.BASE_URL + clean_path_str,
                'path': mmg['path']
            })
        
        return documents

    def download_document(self, url: str, save_path: Union[str, Path], 
                         overwrite: bool = False) -> bool:
        """Download a single document from the given URL.
        
        Args:
            url: The document URL to download
            save_path: Local path to save the file
            overwrite: Whether to overwrite existing files
            
        Returns:
            True if downloaded successfully, False otherwise
        """
        save_path = Path(save_path)
        
        if save_path.exists() and not overwrite:
            print(f"File already exists, skipping: {save_path}")
            return True
            
        try:
            # Create directory if it doesn't exist
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Simple but effective headers for file downloads
            download_headers = {
                "Accept": "application/pdf,application/octet-stream,*/*",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Referer": "https://apps.land.gov.il/TabaSearch/"
            }
            
            # Download with a longer timeout for large files
            response = self.session.get(url, headers=download_headers, timeout=120, stream=True)
            
            # Check status code first
            if response.status_code == 404:
                print(f"File not found (404): {url}")
                return False
            elif response.status_code == 403:
                print(f"Access forbidden (403): {url}")
                return False
            elif response.status_code != 200:
                print(f"HTTP error {response.status_code} for {url}")
                return False
            
            # Check if it's actually a PDF/document (not HTML error page)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                print(f"Warning: Got HTML response instead of document for {url}")
                # Log some of the HTML to understand the error
                html_preview = response.text[:200] if hasattr(response, 'text') else "Cannot read HTML"
                print(f"HTML preview: {html_preview}...")
                return False
            
            # Write file in chunks
            total_size = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
                        
            print(f"Downloaded: {save_path} ({total_size} bytes)")
            return True
            
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False

    def download_plan_documents(self, plan: Dict[str, Any], base_dir: Union[str, Path] = "plans",
                              doc_types: Optional[List[str]] = None, 
                              overwrite: bool = False) -> Dict[str, List[str]]:
        """Download all documents for a single plan.
        
        Args:
            plan: Plan dictionary containing documentsSet
            base_dir: Base directory to save documents
            doc_types: List of document types to download (default: all)
            overwrite: Whether to overwrite existing files
            
        Returns:
            Dict with 'success' and 'failed' lists of file paths
        """
        base_dir = Path(base_dir)
        plan_number = plan.get('planNumber', 'unknown_plan')
        plan_id = plan.get('planId', 'unknown_id')
        
        # Create safe directory name
        safe_plan_name = "".join(c for c in plan_number if c.isalnum() or c in (' ', '-', '_')).strip()
        plan_dir = base_dir / f"{safe_plan_name}_{plan_id}"
        
        documents = self._extract_document_urls(plan)
        
        if doc_types:
            documents = [doc for doc in documents if doc['type'] in doc_types]
            
        results = {'success': [], 'failed': []}
        
        for doc in documents:
            # Create filename from path
            file_path = Path(doc['path'])
            filename = file_path.name
            save_path = plan_dir / doc['type'] / filename
            
            if self.download_document(doc['url'], save_path, overwrite):
                results['success'].append(str(save_path))
            else:
                results['failed'].append(doc['url'])
                
            # Small delay between downloads
            time.sleep(self.delay)
        
        return results

    def download_multiple_plans_documents(self, plans: List[Dict[str, Any]], 
                                        base_dir: Union[str, Path] = "plans",
                                        doc_types: Optional[List[str]] = None,
                                        overwrite: bool = False) -> Dict[str, Any]:
        """Download documents for multiple plans.
        
        Args:
            plans: List of plan dictionaries
            base_dir: Base directory to save documents
            doc_types: List of document types to download (default: all)
            overwrite: Whether to overwrite existing files
            
        Returns:
            Summary of download results
        """
        total_success = 0
        total_failed = 0
        plan_results = {}
        
        for i, plan in enumerate(plans, 1):
            plan_number = plan.get('planNumber', f'plan_{i}')
            print(f"Downloading documents for plan {i}/{len(plans)}: {plan_number}")
            
            results = self.download_plan_documents(plan, base_dir, doc_types, overwrite)
            plan_results[plan_number] = results
            
            total_success += len(results['success'])
            total_failed += len(results['failed'])
            
            print(f"  ✓ {len(results['success'])} files downloaded, ✗ {len(results['failed'])} failed")
        
        summary = {
            'total_plans': len(plans),
            'total_files_downloaded': total_success,
            'total_files_failed': total_failed,
            'plan_results': plan_results
        }
        
        print("\nDownload Summary:")
        print(f"Plans processed: {summary['total_plans']}")
        print(f"Files downloaded: {summary['total_files_downloaded']}")
        print(f"Files failed: {summary['total_files_failed']}")
        
        return summary


__all__ = ["RamiClient"]
