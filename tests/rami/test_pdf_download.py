#!/usr/bin/env python3
"""Test PDF downloading functionality for RamiClient."""

import json
from pathlib import Path

import tests.utils.test_utils  # This sets up the Python path
from gov.rami.rami_client import RamiClient


def test_document_extraction():
    """Test extracting document URLs from plan data."""
    client = RamiClient()
    
    # Mock plan data based on the user's example
    mock_plan = {
        'planNumber': 'תגפ/515',
        'planId': 5005390,
        'cityText': 'אור יהודה',
        'documentsSet': {
            'takanon': {
                'path': '/IturTabotData/takanonim/telmer/5005390.pdf',
                'info': 'תקנון סרוק'
            },
            'tasritim': [
                {
                    'path': '/IturTabotData\\tabot\\telmer\\5005390.pdf',
                    'info': 'תשריט'
                }
            ],
            'nispachim': [],
            'mmg': {
                'path': '/IturTabotData\\download\\telmer\\5005390.zip',
                'info': 'הורדת קבצי ממג 1.9326171875 MB'
            }
        }
    }
    
    # Extract document URLs
    documents = client._extract_document_urls(mock_plan)
    
    print(f"Extracted {len(documents)} documents:")
    for doc in documents:
        print(f"  - {doc['type']}: {doc['name']}")
        print(f"    URL: {doc['url']}")
        print()
    
    return documents


def test_limited_download():
    """Test downloading a few documents from real Tel Aviv plans."""
    client = RamiClient()
    
    # Search for Tel Aviv plans (limited search)
    search_params = {
        'planNumber': '',
        'city': 5000,  # Tel Aviv
        'block': '',
        'parcel': '',
        'statuses': None,
        'planTypes': [72, 21],  # Limited plan types for testing
        'fromStatusDate': None,
        'toStatusDate': None,
        'planTypesUsed': False
    }
    
    try:
        print("Fetching Tel Aviv plans...")
        df = client.fetch_plans(search_params)
        
        if len(df) == 0:
            print("No plans found")
            return
            
        print(f"Found {len(df)} plans")
        
        # Take only first 2 plans for testing
        test_plans = df.head(2).to_dict('records')
        
        print(f"Testing download with {len(test_plans)} plans")
        
        # Download only takanon (regulations) documents to limit download size
        results = client.download_multiple_plans_documents(
            test_plans, 
            base_dir="test_downloads",
            doc_types=['takanon'],  # Only regulations for testing
            overwrite=False
        )
        
        print("\nTest Download Results:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Check if files were actually created
        test_dir = Path("test_downloads")
        if test_dir.exists():
            print(f"\nFiles in {test_dir}:")
            for file_path in test_dir.rglob("*"):
                if file_path.is_file():
                    print(f"  {file_path} ({file_path.stat().st_size} bytes)")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_single_plan_download():
    """Test downloading documents for a single plan with known structure."""
    client = RamiClient()
    
    # Mock a complete plan based on user's data
    test_plan = {
        'planNumber': 'תמ"א 10/ג/12',
        'planId': 5050330,
        'cityText': 'בני ברק',
        'documentsSet': {
            'takanon': {
                'path': '/IturTabotData/takanonim/telmer/5050330.pdf',
                'info': 'תקנון סרוק'
            },
            'tasritim': [
                {
                    'path': '/IturTabotData\\tabot\\telmer\\5050330\\5050330_מצב מאושר-גיליון 1.pdf',
                    'info': '5050330_מצב מאושר-גיליון 1'
                },
                {
                    'path': '/IturTabotData\\tabot\\telmer\\5050330\\5050330_מצב מאושר-גיליון 2.pdf',
                    'info': '5050330_מצב מאושר-גיליון 2'
                }
            ],
            'nispachim': [
                {
                    'path': '/IturTabotData\\nispachim\\telmer\\5050330\\46.pdf',
                    'info': 'חתכים'
                }
            ],
            'mmg': {
                'path': '/IturTabotData\\download\\telmer\\5050330.zip',
                'info': 'הורדת קבצי ממג 1 MB'
            }
        }
    }
    
    print("Testing single plan document download...")
    print(f"Plan: {test_plan['planNumber']} ({test_plan['cityText']})")
    
    # Extract documents first
    documents = client._extract_document_urls(test_plan)
    print(f"Found {len(documents)} documents to download:")
    for doc in documents:
        print(f"  - {doc['type']}: {doc['name']}")
    
    # Download only takanon for testing
    results = client.download_plan_documents(
        test_plan,
        base_dir="single_plan_test",
        doc_types=['takanon'],  # Only regulations
        overwrite=True
    )
    
    print(f"\nDownload results: {results}")


if __name__ == "__main__":
    print("=== Testing Document Extraction ===")
    test_document_extraction()
    
    print("\n=== Testing Single Plan Download ===")
    test_single_plan_download()
    
    print("\n=== Testing Limited Real Download ===") 
    test_limited_download()
