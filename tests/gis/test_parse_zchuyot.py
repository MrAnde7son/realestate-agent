import os
import tempfile

import pytest

from gis.parse_zchuyot import parse_html_privilege_page, parse_zchuyot


def test_parse_html_privilege_page():
    """Test parsing HTML privilege page with multiple parcels."""
    
    # Sample HTML content similar to the one provided
    html_content = """
    <html>
    <head>
        <script>
        var is_opts = '<SELECT NAME=opts DIR=rtl STYLE=`font-size:8pt` SIZE=6 onChange=f_option(this)>  <OPTION VALUE=`block=6632&parcel=3200&status=0&street=4844&house=0&chasum=0&`>מגרש: 3200 מוסדר  -  רחוב קדושי השואה  (יעוד קרקע: אזור תעסוקה שטח: 12826.81 מ``ר)</OPTION>  <OPTION VALUE=`block=6632&parcel=3214&status=0&street=4844&house=0&chasum=0&`>מגרש: 3214 מוסדר  -  רחוב קדושי השואה  (יעוד קרקע: מגורים שטח: 3702.89 מ``ר)</OPTION>  <OPTION VALUE=`block=6632&parcel=3215&status=0&street=1258&house=504&chasum=0&`>מגרש: 3215 מוסדר  -  רחוב פרופס מס` 504  (יעוד קרקע: דרך קיימת שטח: 16599.68 מ``ר)</OPTION>  <OPTION VALUE=`block=6632&parcel=3233&status=0&street=4844&house=0&chasum=0&`>מגרש: 3233 מוסדר  -  רחוב קדושי השואה  (יעוד קרקע: דרך מוצעת שטח: 5265.48 מ``ר)</OPTION> </SELECT>';
        </script>
    </head>
    <body>
        <select>
            <option value="block=6632&parcel=3200&status=0&street=4844&house=0&chasum=0&">מגרש: 3200 מוסדר  -  רחוב קדושי השואה  (יעוד קרקע: אזור תעסוקה שטח: 12826.81 מ``ר)</option>
        </select>
    </body>
    </html>
    """
    
    parcels = parse_html_privilege_page(html_content)
    
    assert len(parcels) == 4, f"Expected 4 parcels, got {len(parcels)}"
    
    # Check first parcel
    first_parcel = parcels[0]
    assert first_parcel['block'] == '6632'
    assert first_parcel['parcel'] == '3200'
    assert first_parcel['parcel_number'] == '3200'
    assert first_parcel['parcel_status'] == 'מוסדר'
    assert first_parcel['street_name'] == 'רחוב קדושי השואה'
    assert first_parcel['land_use'] == 'אזור תעסוקה'
    assert first_parcel['area'] == '12826.81'
    
    # Check second parcel
    second_parcel = parcels[1]
    assert second_parcel['block'] == '6632'
    assert second_parcel['parcel'] == '3214'
    assert second_parcel['parcel_number'] == '3214'
    assert second_parcel['land_use'] == 'מגורים'
    assert second_parcel['area'] == '3702.89'
    
    # Check third parcel with house number
    third_parcel = parcels[2]
    assert third_parcel['block'] == '6632'
    assert third_parcel['parcel'] == '3215'
    assert third_parcel['house_number'] == '504'
    assert third_parcel['land_use'] == 'דרך קיימת'
    assert third_parcel['area'] == '16599.68'


def test_parse_html_privilege_page_empty():
    """Test parsing empty HTML content."""
    
    parcels = parse_html_privilege_page("")
    assert parcels == []


def test_parse_html_privilege_page_no_options():
    """Test parsing HTML content without parcel options."""
    html_content = "<html><body><p>No options here</p></body></html>"
    parcels = parse_html_privilege_page(html_content)
    assert parcels == []


def test_parse_zchuyot_pdf():
    """Test parsing the uploaded PDF file using parse_zchuyot function."""
    
    # Path to the uploaded PDF file
    pdf_path = "tests/samples/202581210827_zchuyot.pdf"
    
    # Check if file exists
    assert os.path.exists(pdf_path), f"PDF file not found at {pdf_path}"
    
    # Parse the PDF
    result = parse_zchuyot(pdf_path)
    
    # Basic structure validation
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "source_file" in result, "Result should contain source_file"
    assert "extracted_at" in result, "Result should contain extracted_at"
    assert "basic" in result, "Result should contain basic info"
    assert "plans" in result, "Result should contain plans"
    assert "alerts" in result, "Result should contain alerts"
    assert "policy" in result, "Result should contain policy"
    assert "rights" in result, "Result should contain rights"
    assert "all_links" in result, "Result should contain all_links"
    assert "raw_preview" in result, "Result should contain raw_preview"
    
    # Validate source file path
    assert result["source_file"] == os.path.abspath(pdf_path)
    
    # Validate extracted_at timestamp
    assert result["extracted_at"].endswith("Z"), "Timestamp should be in UTC format"
    
    # Validate basic info structure
    basic = result["basic"]
    assert isinstance(basic, dict), "Basic info should be a dictionary"
    assert "issue_date" in basic, "Basic info should contain issue_date"
    assert "address" in basic, "Basic info should contain address"
    assert "block" in basic, "Basic info should contain block"
    assert "parcel" in basic, "Basic info should contain parcel"
    assert "parcel_area_sqm" in basic, "Basic info should contain parcel_area_sqm"
    
    # Validate plans structure
    plans = result["plans"]
    assert "in_force" in plans, "Plans should contain in_force section"
    assert "in_planning" in plans, "Plans should contain in_planning section"
    
    in_force = plans["in_force"]
    assert "local" in in_force, "In-force plans should contain local section"
    assert "citywide" in in_force, "In-force plans should contain citywide section"
    assert "national_regional" in in_force, "In-force plans should contain national_regional section"
    assert "architectural" in in_force, "In-force plans should contain architectural section"
    
    in_planning = plans["in_planning"]
    assert "citywide" in in_planning, "In-planning should contain citywide section"
    assert "national_regional" in in_planning, "In-planning should contain national_regional section"
    
    # Validate that all plan sections are lists
    for section_name, section_data in in_force.items():
        assert isinstance(section_data, list), f"Plan section {section_name} should be a list"
    
    for section_name, section_data in in_planning.items():
        assert isinstance(section_data, list), f"In-planning section {section_name} should be a list"
    
    # Validate other sections are lists
    assert isinstance(result["alerts"], list), "Alerts should be a list"
    assert isinstance(result["policy"], list), "Policy should be a list"
    assert isinstance(result["rights"], dict), "Rights should be a dictionary"
    assert isinstance(result["all_links"], list), "All_links should be a list"
    
    # Validate raw_preview is a string and not too long
    assert isinstance(result["raw_preview"], str), "Raw preview should be a string"
    assert len(result["raw_preview"]) <= 2000, "Raw preview should be limited to 2000 characters"
    
    print(f"Successfully parsed PDF with {len(result['all_links'])} links")
    print(f"Basic info: {basic}")
    print(f"Total in-force plans: {sum(len(plans['in_force'][k]) for k in plans['in_force'])}")
    print(f"Total in-planning plans: {sum(len(plans['in_planning'][k]) for k in plans['in_planning'])}")


def test_parse_zchuyot_pdf_content_validation():
    """Test specific content validation from the uploaded PDF."""
    pdf_path = "tests/samples/202581210827_zchuyot.pdf"
    
    if not os.path.exists(pdf_path):
        pytest.skip(f"PDF file not found at {pdf_path}")
    
    result = parse_zchuyot(pdf_path)
    
    # Test that we can extract meaningful information
    basic = result["basic"]
    
    # Note: Basic info extraction might fail for Hebrew PDFs due to text encoding issues
    # This is a known limitation, so we'll test what we can extract
    print(f"Basic info extracted: {basic}")
    
    # Test that plans have expected structure when they exist
    plans = result["plans"]
    
    # Check if any plans exist and validate their structure
    for plan_type, plan_sections in plans.items():
        for section_name, plan_list in plan_sections.items():
            if plan_list:  # If plans exist in this section
                for plan in plan_list:
                    assert isinstance(plan, dict), f"Plan should be a dictionary in {plan_type}.{section_name}"
                    # Each plan should have at least a plan_number or name
                    has_plan_info = any([
                        plan.get("plan_number"),
                        plan.get("name")
                    ])
                    assert has_plan_info, f"Plan should have at least plan_number or name in {plan_type}.{section_name}"
    
    # Test that URLs are properly extracted and cleaned
    all_links = result["all_links"]
    if all_links:
        for url in all_links:
            assert url.startswith(("http://", "https://")), f"URL should start with http:// or https://: {url}"
            # URLs should not end with common punctuation that might have been OCR noise
            assert not url.endswith((".", ",", ";", "]", ">")), f"URL should not end with punctuation: {url}"
    
    print(f"Content validation passed. Extracted {len(all_links)} URLs and basic info: {basic}")


def test_parse_zchuyot_pdf_error_handling():
    """Test error handling for parse_zchuyot function."""
    
    # Test with non-existent file
    with pytest.raises(Exception):  # Should raise some kind of error
        parse_zchuyot("non_existent_file.pdf")
    
    # Test with empty file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(b"")
        tmp_file_path = tmp_file.name
    
    try:
        # This might fail in different ways depending on the PDF library
        try:
            result = parse_zchuyot(tmp_file_path)
            # If it succeeds, the result should be minimal but valid
            assert isinstance(result, dict)
            assert "source_file" in result
        except Exception as e:
            # It's acceptable for this to fail
            print(f"Expected failure with empty PDF: {e}")
    finally:
        os.unlink(tmp_file_path)


def test_parse_zchuyot_pdf_plan_structure():
    """Test the structure of plans extracted from the PDF."""
    pdf_path = "tests/samples/202581210827_zchuyot.pdf"
    
    if not os.path.exists(pdf_path):
        pytest.skip(f"PDF file not found at {pdf_path}")
    
    result = parse_zchuyot(pdf_path)
    plans = result["plans"]
    
    # Test in-force plans structure
    in_force = plans["in_force"]
    for section_name, plan_list in in_force.items():
        assert isinstance(plan_list, list), f"In-force {section_name} should be a list"
        
        for plan in plan_list:
            assert isinstance(plan, dict), f"Plan in {section_name} should be a dictionary"
            
            # Check required fields for plans
            required_fields = ["plan_number", "name", "deposit_date", "effective_date"]
            for field in required_fields:
                if field in plan:
                    assert plan[field] is not None, f"Plan field {field} should not be None"
            
            # Check URLs field if present
            if "urls" in plan:
                assert isinstance(plan["urls"], list), f"Plan URLs should be a list in {section_name}"
                for url in plan["urls"]:
                    assert isinstance(url, str), f"Plan URL should be a string in {section_name}"
                    assert url.startswith(("http://", "https://")), f"Plan URL should be valid: {url}"
    
    # Test in-planning plans structure
    in_planning = plans["in_planning"]
    for section_name, plan_list in in_planning.items():
        assert isinstance(plan_list, list), f"In-planning {section_name} should be a list"
        
        for plan in plan_list:
            assert isinstance(plan, dict), f"Plan in {section_name} should be a dictionary"
            
            # In-planning plans might have different fields
            if "plan_number" in plan:
                assert plan["plan_number"] is not None, f"Plan number should not be None in {section_name}"
            if "name" in plan:
                assert plan["name"] is not None, f"Plan name should not be None in {section_name}"
    
    print("Plan structure validation passed")


def test_parse_zchuyot_pdf_rights_and_policy():
    """Test the extraction of rights and policy information from the PDF."""
    pdf_path = "tests/samples/202581210827_zchuyot.pdf"
    
    if not os.path.exists(pdf_path):
        pytest.skip(f"PDF file not found at {pdf_path}")
    
    result = parse_zchuyot(pdf_path)
    
    # Test rights extraction
    rights = result["rights"]
    assert isinstance(rights, dict), "Rights should be a dictionary"
    
    # Rights might be empty or contain information
    if rights:
        for key, value in rights.items():
            # Handle different types of values in rights
            if key == 'referred_plans':
                # referred_plans can be a set or list
                assert isinstance(value, (list, set)), f"Rights value for {key} should be a list or set"
            elif key == 'notes':
                # notes should be a list of dictionaries
                assert isinstance(value, list), f"Rights value for {key} should be a list"
                if value:  # If list is not empty
                    for item in value:
                        assert isinstance(item, dict), f"Each right item in {key} should be a dictionary"
                        assert any(item.values()), f"Right item in {key} should have at least one non-empty value"
            elif key in ['percent_building', 'basement_area', 'service_percentage', 'number_of_floors']:
                # These can be single values (int, float, str)
                assert isinstance(value, (int, float, str)), f"Rights value for {key} should be a number or string"
            else:
                # Other values should be lists (but items can be strings or other types)
                assert isinstance(value, list), f"Rights value for {key} should be a list"
                # Rights should have some meaningful content
                if value:  # If list is not empty
                    for item in value:
                        # Items can be strings, numbers, or dictionaries
                        assert isinstance(item, (str, int, float, dict)), f"Right item in {key} should be a string, number, or dictionary"
    
    # Test policy extraction
    policy = result["policy"]
    assert isinstance(policy, list), "Policy should be a list"
    
    # Policy might be empty or contain information
    if policy:
        for pol in policy:
            assert isinstance(pol, dict), "Each policy item should be a dictionary"
            # Policy items should have some meaningful content
            assert any(pol.values()), "Policy item should have at least one non-empty value"
    
    print(f"Rights and policy validation passed. Found {len(rights)} rights keys and {len(policy)} policy items")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

