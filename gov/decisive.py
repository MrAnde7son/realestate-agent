from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

import requests

from .constants import DEFAULT_TIMEOUT


@dataclass
class DecisiveAppraisal:
    """Data class representing a decisive appraisal decision."""
    
    title: str
    date: str
    appraiser: str
    committee: str
    pdf_url: str
    appraisal_type: str = ""
    appraisal_version: str = ""
    appraiser_type: str = ""
    block: str = ""
    plot: str = ""
    publicity_date: str = ""
    
    def get_pdf_urls(self) -> List[str]:
        """Get list of individual PDF URLs."""
        if not self.pdf_url:
            return []
        return [url.strip() for url in self.pdf_url.split(";") if url.strip()]
    
    def to_dict(self) -> Dict[str, str]:
        """Convert the appraisal to a dictionary."""
        return {
            "title": self.title,
            "date": self.date,
            "appraiser": self.appraiser,
            "committee": self.committee,
            "pdf_url": self.pdf_url,
            "appraisal_type": self.appraisal_type,
            "appraisal_version": self.appraisal_version,
            "appraiser_type": self.appraiser_type,
            "block": self.block,
            "plot": self.plot,
            "publicity_date": self.publicity_date,
        }


class DecisiveAppraisalParser(ABC):
    """Abstract base class for parsing decisive appraisal data."""
    
    @abstractmethod
    def parse(self, data: Dict) -> List[DecisiveAppraisal]:
        """Parse raw data into DecisiveAppraisal objects."""
        pass


class APIDecisiveAppraisalParser(DecisiveAppraisalParser):
    """Parser for API response data."""
    
    def parse(self, response_data: Dict) -> List[DecisiveAppraisal]:
        """Parse API response data into DecisiveAppraisal objects."""
        appraisals = []
        
        if "Results" not in response_data:
            return appraisals
        
        for result in response_data["Results"]:
            if "Data" not in result:
                continue
                
            data = result["Data"]
            appraisal = self._create_appraisal_from_data(data)
            appraisals.append(appraisal)
        
        return appraisals
    
    def _create_appraisal_from_data(self, data: Dict) -> DecisiveAppraisal:
        """Create a DecisiveAppraisal object from API data."""
        # Extract all document URLs
        pdf_urls = []
        if "Document" in data and data["Document"]:
            for document in data["Document"]:
                url = document.get("FileName", "")
                if url:
                    pdf_urls.append(url)
        
        # Join all URLs with semicolon separator for backward compatibility
        pdf_url = "; ".join(pdf_urls)
        
        # Format the date from ISO format to DD.MM.YYYY
        decision_date = self._format_date(data.get("DecisionDate", ""))
        
        return DecisiveAppraisal(
            title=data.get("AppraisalHeader", ""),
            date=decision_date,
            appraiser=data.get("DecisiveAppraiser", ""),
            committee=data.get("Committee", ""),
            pdf_url=pdf_url,
            appraisal_type=data.get("AppraisalType", ""),
            appraisal_version=data.get("AppraisalVersion", ""),
            appraiser_type=data.get("AppraiserType", ""),
            block=data.get("Block", ""),
            plot=data.get("Plot", ""),
            publicity_date=data.get("PublicityDate", ""),
        )
    
    def _format_date(self, iso_date: str) -> str:
        """Format ISO date to DD.MM.YYYY format."""
        if not iso_date:
            return ""
        
        try:
            # Parse ISO date format: "2025-09-01T00:00:00+03:00"
            date_part = iso_date.split("T")[0]  # "2025-09-01"
            year, month, day = date_part.split("-")
            return f"{day}.{month}.{year}"
        except (ValueError, IndexError):
            return ""


class DecisiveAppraisalClient:
    """Client for fetching decisive appraisal decisions from gov.il API."""
    
    def __init__(
        self, 
        parser: Optional[DecisiveAppraisalParser] = None,
        timeout: float = DEFAULT_TIMEOUT
    ):
        self.api_endpoint = (
            "https://pub-justice.openapi.gov.il/pub/moj/portal/rest/searchpredefinedapi/v1/"
            "SearchPredefinedApi/DecisiveAppraiser/SearchDecisions"
        )
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "content-type": "application/json;charset=UTF-8",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "x-client-id": "149a5bad-edde-49a6-9fb9-188bd17d4788"
        }
        self.parser = parser or APIDecisiveAppraisalParser()
        self.timeout = timeout
    
    def fetch_appraisals(
        self, 
        block: str = "", 
        plot: str = "", 
        max_pages: int = 1
    ) -> List[DecisiveAppraisal]:
        """
        Fetch decisive appraisal decisions from the gov.il API.
        
        Args:
            block: Block number to search for
            plot: Plot number to search for  
            max_pages: Maximum number of pages to fetch (each page has 10 results)
            
        Returns:
            List of DecisiveAppraisal objects
        """
        all_appraisals: List[DecisiveAppraisal] = []
        
        for page in range(max_pages):
            # Calculate skip value (10 results per page)
            skip = page * 10
            
            # Prepare request body
            request_body = {
                "skip": skip,
                "Block": block,
                "Plot": plot
            }
            
            try:
                # Make API request
                response = requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=request_body,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Parse response
                response_data = response.json()
                appraisals = self.parser.parse(response_data)
                
                # If no appraisals returned, break the loop
                if not appraisals:
                    break
                    
                all_appraisals.extend(appraisals)
                
                # Check if we've reached the total results
                total_results = response_data.get("TotalResults", 0)
                if len(all_appraisals) >= total_results:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching decisive appraisals: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"Error parsing API response: {e}")
                break
        
        return all_appraisals







if __name__ == "__main__":
    results = DecisiveAppraisalClient().fetch_appraisals(block="8733",plot="15", max_pages=1)
    print(results)