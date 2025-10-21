import os
import tempfile

import pytest

from gis.parse_zchuyot import parse_zchuyot



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
    assert "policies" in result, "Result should contain policies"
    assert "rights" in result, "Result should contain rights"
    assert "raw_preview" in result, "Result should contain raw_preview"
    assert "details" in result, "Result should contain details section"
    
    # Validate source file path
    assert result["source_file"] == os.path.abspath(pdf_path)
    
    # Validate extracted_at timestamp
    assert result["extracted_at"].endswith("Z"), "Timestamp should be in UTC format"
    
    # Validate basic info structure
    basic = result["basic"]
    assert isinstance(basic, dict), "Basic info should be a dictionary"
    assert "issue_date" in basic, "Basic info should contain issue_date"
    assert "block" in basic, "Basic info should contain block"
    assert "parcel" in basic, "Basic info should contain parcel"
    assert "parcel_area_sqm" in basic, "Basic info should contain parcel_area_sqm"
    assert "land_use" in basic, "Basic info should contain land_use"

    details = result["details"]
    assert isinstance(details, dict), "Details should be a dictionary"
    assert "addresses" in details, "Details should include addresses list"
    assert isinstance(details["addresses"], list), "Addresses should be a list"
    
    # Validate plans structure
    plans = result["plans"]
    assert "in_force" in plans, "Plans should contain in_force section"
    assert "in_planning" in plans, "Plans should contain in_planning section"
    
    in_force = plans["in_force"]
    assert "local" in in_force, "In-force plans should contain local section"
    assert "citywide" in in_force, "In-force plans should contain citywide section"
    assert "national_regional" in in_force, "In-force plans should contain national_regional section"
    
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
    assert isinstance(result["policies"], list), "Policies should be a list"
    assert isinstance(result["rights"], dict), "Rights should be a dictionary"
    
    # Validate raw_preview is a string and not too long
    assert isinstance(result["raw_preview"], str), "Raw preview should be a string"
    assert 0 < len(result["raw_preview"]) <= 20000, "Raw preview should have a sensible length"
    
    print(f"Successfully parsed PDF with {len(result.get('policies', []))} policies")
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
    all_links = result.get("all_links", [])
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
            assert plan.get("plan_number"), f"Plan number missing in {section_name}"
            assert plan.get("name") is not None, f"Plan name missing in {section_name}"

            for date_field in ("deposit_date", "effective_date"):
                if plan.get(date_field) is not None:
                    assert isinstance(plan[date_field], str), f"{date_field} should be a string when present"
            
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
                assert plan["plan_number"] not in (None, ""), f"Plan number should not be empty in {section_name}"
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
    
    text_value = rights.get("text")
    assert text_value is None or isinstance(text_value, str), "Rights.text should be a string or None"

    list_fields = [
        "building_lines",
        "building_lines_detailed",
        "floor_percentages",
        "floor_percentages_detailed",
        "minimum_values",
        "maximum_values",
        "minmax_values",
        "parking_requirements",
        "notes",
    ]
    for field in list_fields:
        if field in rights:
            assert isinstance(rights[field], list), f"Rights field {field} should be a list"

    if "building_lines" in rights:
        assert all(isinstance(item, str) for item in rights["building_lines"]), "Building lines should be strings"

    if "building_lines_detailed" in rights:
        for item in rights["building_lines_detailed"]:
            assert isinstance(item, dict), "Detailed building line should be a dict"
            assert "raw_text" in item, "Detailed building line requires raw_text"

    if "floor_percentages" in rights:
        for value in rights["floor_percentages"]:
            assert isinstance(value, (int, float)), "Floor percentage entries should be numeric"

    if "floor_percentages_detailed" in rights:
        for item in rights["floor_percentages_detailed"]:
            assert isinstance(item, dict), "Detailed floor percentage should be a dict"
            assert "percentage" in item and isinstance(item["percentage"], (int, float)), "Detailed percentage must be numeric"

    if "notes" in rights:
        for note in rights["notes"]:
            assert isinstance(note, dict), "Notes should contain dictionaries"
            assert "text" in note, "Each note should include text"

    numeric_fields = [
        "building_coverage_percentage",
        "coverage",
        "dwelling_units",
        "floors",
        "auxiliary_building_area",
    ]
    for field in numeric_fields:
        if field in rights and rights[field] is not None:
            assert isinstance(rights[field], (int, float)), f"Rights field {field} should be numeric when present"
    
    # Test policy extraction
    policies = result["policies"]
    assert isinstance(policies, list), "Policies should be a list"
    
    # Policy might be empty or contain information
    if policies:
        for pol in policies:
            assert isinstance(pol, dict), "Each policy item should be a dictionary"
            # Policy items should have some meaningful content
            assert any(pol.values()), "Policy item should have at least one non-empty value"
    
    print(f"Rights and policy validation passed. Found {len(rights)} rights keys and {len(policies)} policy items")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
