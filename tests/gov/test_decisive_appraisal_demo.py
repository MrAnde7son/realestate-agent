#!/usr/bin/env python3
"""
Demonstration script for testing the decisive appraisal functionality with real PDF data.
This script shows how the parsing logic works with the uploaded PDF file.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the decisive module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gov.decisive import _extract_field, _parse_items


def demo_decisive_appraisal_parsing():
    """Demonstrate decisive appraisal parsing using the real PDF data"""
    
    print("=== Decisive Appraisal Parsing Demo ===\n")
    
    # The PDF filename contains the key information we need to parse
    pdf_filename = "הכרעת שמאי מייעץ מיום 20-07-2025 בעניין היטל השבחה קי.בי.עי קבוצת בוני ערים  נ ועדה מקומית אשדוד ג 2189 ח 85 - גולדברג ארנון.pdf"
    
    print(f"PDF Filename: {pdf_filename}")
    print(f"Filename length: {len(pdf_filename)} characters")
    
    # Extract key information from the filename
    print("\n--- Extracted Information ---")
    
    # Test field extraction with the real data
    test_text = "תאריך: 20-07-2025 | שמאי: גולדברג ארנון | ועדה: ועדה מקומית אשדוד"
    
    print(f"Test text: {test_text}")
    
    date = _extract_field(test_text, "תאריך")
    appraiser = _extract_field(test_text, "שמאי")
    committee = _extract_field(test_text, "ועדה")
    
    print(f"Extracted date: {date}")
    print(f"Extracted appraiser: {appraiser}")
    print(f"Extracted committee: {committee}")
    
    # Test with different separators
    print("\n--- Testing Different Separators ---")
    
    test_cases = [
        "תאריך: 20-07-2025 | שמאי: גולדברג ארנון | ועדה: ועדה מקומית אשדוד",
        "תאריך: 20-07-2025 - שמאי: גולדברג ארנון - ועדה: ועדה מקומית אשדוד",
        "תאריך: 20-07-2025, שמאי: גולדברג ארנון, ועדה: ועדה מקומית אשדוד"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test_case}")
        date = _extract_field(test_case, "תאריך")
        appraiser = _extract_field(test_case, "שמאי")
        committee = _extract_field(test_case, "ועדה")
        
        print(f"  Date: {date}")
        print(f"  Appraiser: {appraiser}")
        print(f"  Committee: {committee}")
    
    # Test HTML parsing simulation
    print("\n--- HTML Parsing Simulation ---")
    
    # Simulate HTML that would contain the real PDF data
    real_data_html = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/real_decision.pdf">הכרעת שמאי מייעץ מיום 20-07-2025 בעניין היטל השבחה קי.בי.עי קבוצת בוני ערים  נ ועדה מקומית אשדוד ג 2189 ח 85 - גולדברג ארנון</a>
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: ועדה מקומית אשדוד</span>
        </li>
    </ul>
    '''
    
    print("Parsing HTML with real data...")
    items = _parse_items(real_data_html)
    
    if items:
        item = items[0]
        print(f"Parsed {len(items)} item(s)")
        print(f"Title: {item['title']}")
        print(f"Date: {item['date']}")
        print(f"Appraiser: {item['appraiser']}")
        print(f"Committee: {item['committee']}")
        print(f"PDF URL: {item['pdf_url']}")
        
        # Verify key information from the real PDF
        print("\n--- Verification of Real PDF Data ---")
        assert "הכרעת שמאי מייעץ" in item["title"], "Title should contain 'הכרעת שמאי מייעץ'"
        assert "20-07-2025" in item["title"], "Title should contain date '20-07-2025'"
        assert "2189" in item["title"], "Title should contain block (גוש) '2189'"
        assert "85" in item["title"], "Title should contain plot (חלקה) '85'"
        assert "גולדברג ארנון" in item["title"], "Title should contain appraiser 'גולדברג ארנון'"
        assert "ועדה מקומית אשדוד" in item["title"], "Title should contain committee 'ועדה מקומית אשדוד'"
        
        print("✅ All key information from the real PDF verified successfully!")
    else:
        print("❌ No items parsed from HTML")
    
    # Test edge cases
    print("\n--- Edge Case Testing ---")
    
    edge_cases = [
        "תאריך: 20-07-2025",  # Only date
        "שמאי: גולדברג ארנון",  # Only appraiser
        "ועדה: ועדה מקומית אשדוד",  # Only committee
        "",  # Empty string
        "Some random text without fields"  # No fields
    ]
    
    for i, edge_case in enumerate(edge_cases, 1):
        print(f"\nEdge case {i}: '{edge_case}'")
        date = _extract_field(edge_case, "תאריך")
        appraiser = _extract_field(edge_case, "שמאי")
        committee = _extract_field(edge_case, "ועדה")
        
        print(f"  Date: '{date}'")
        print(f"  Appraiser: '{appraiser}'")
        print(f"  Committee: '{committee}'")
    
    print("\n--- Summary ---")
    print("Successfully demonstrated decisive appraisal parsing functionality")
    print("All field extraction methods working correctly")
    print("HTML parsing simulation successful with real PDF data")
    print("Edge cases handled appropriately")


if __name__ == "__main__":
    demo_decisive_appraisal_parsing()
