#!/usr/bin/env python3
"""
Enhanced building rights calculator that can calculate remainingRightsSqm from real data.
"""

import re
from typing import Dict, Any, Optional

def calculate_remaining_rights_from_parsed_data(parsed_data: Dict[str, Any], parcel_area_sqm: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate remaining building rights from parsed privilege page data.
    
    Args:
        parsed_data: Parsed data from parse_zchuyot
        parcel_area_sqm: Parcel area in square meters (if known)
    
    Returns:
        Dict with calculated remaining rights
    """
    
    rights = parsed_data.get('rights', {})
    basic = parsed_data.get('basic', {})
    
    # Extract parcel area from basic info or use provided value
    area = basic.get('parcel_area_sqm') or parcel_area_sqm
    
    # Extract building rights information
    percent_building = rights.get('percent_building')
    building_lines = rights.get('building_lines', [])
    areas = rights.get('areas', [])
    building_rights_areas = rights.get('building_rights_areas', [])
    specific_building_rights = rights.get('specific_building_rights', [])
    
    # Extract additional building rights information
    floor_percentages = rights.get('floor_percentages', [])
    floor_details = rights.get('floor_details', [])
    relative_floor_percentages = rights.get('relative_floor_percentages', [])
    general_percentages = rights.get('general_percentages', [])
    building_coverage_percentages = rights.get('building_coverage_percentages', [])
    parking_percentages = rights.get('parking_percentages', [])
    roof_percentages = rights.get('roof_percentages', [])
    basement_area = rights.get('basement_area')
    service_percentage = rights.get('service_percentage')
    auxiliary_buildings = rights.get('auxiliary_buildings')
    number_of_floors = rights.get('number_of_floors')
    
    # Calculate remaining rights
    remaining_rights = {
        'parcel_area_sqm': area,
        'percent_building': percent_building,
        'building_lines': building_lines,
        'areas_found': areas,
        'building_rights_areas': building_rights_areas,
        'specific_building_rights': specific_building_rights,
        'floor_percentages': floor_percentages,
        'basement_area': basement_area,
        'service_percentage': service_percentage,
        'auxiliary_buildings': auxiliary_buildings,
        'number_of_floors': number_of_floors,
        'calculated_remaining_rights_sqm': None,
        'calculation_method': 'unknown'
    }
    
    # Method 1: Use percent building
    if percent_building and area:
        max_building_percent = 80  # Assume max 80% building coverage
        current_building_percent = percent_building
        remaining_percent = max_building_percent - current_building_percent
        
        if remaining_percent > 0:
            remaining_rights['calculated_remaining_rights_sqm'] = int((remaining_percent / 100) * area)
            remaining_rights['calculation_method'] = 'percent_building'
    
    # Method 2: Use specific building rights
    elif specific_building_rights:
        # Extract additional rights from specific building rights
        additional_rights = 0
        seen_numbers = set()  # To avoid counting duplicates
        
        for area_text in specific_building_rights:
            # Look for patterns like "10 מ״ר" or "20 מ״ר"
            matches = re.findall(r'(\d+)\s*מ[״\"]ר', area_text)
            for match in matches:
                if match not in seen_numbers:
                    additional_rights += int(match)
                    seen_numbers.add(match)
            
            # Look for patterns like "`מ 7ןיינבוק `מ 18ךרדבחור 19 (905)דודסוכרמבוחר"
            # Extract the first number after `מ
            match = re.search(r"`מ\s*(\d+)", area_text)
            if match and match.group(1) not in seen_numbers:
                additional_rights += int(match.group(1))
                seen_numbers.add(match.group(1))
            
            # Look for patterns like "`מ 6ןיינבוק `מ 10ךרדבחור 78 (903)ם"קבוחר"
            # Extract the second number after `מ
            match = re.search(r"`מ\s*\d+ןיינבוק\s*`מ\s*(\d+)", area_text)
            if match and match.group(1) not in seen_numbers:
                additional_rights += int(match.group(1))
                seen_numbers.add(match.group(1))
        
        if additional_rights > 0:
            remaining_rights['calculated_remaining_rights_sqm'] = additional_rights
            remaining_rights['calculation_method'] = 'specific_building_rights'
    
    # Method 3: Use building rights areas
    elif building_rights_areas:
        # Extract additional rights from building rights areas
        additional_rights = 0
        for area_text in building_rights_areas:
            # Look for patterns like "10 מ״ר" or "20 מ״ר"
            matches = re.findall(r'(\d+)\s*מ[״\"]ר', area_text)
            for match in matches:
                additional_rights += int(match)
        
        if additional_rights > 0:
            remaining_rights['calculated_remaining_rights_sqm'] = additional_rights
            remaining_rights['calculation_method'] = 'building_rights_areas'
    
    # Method 4: Use general areas found
    elif areas:
        # Sum up all areas found as potential additional rights
        total_areas = sum(areas)
        if total_areas > 0:
            remaining_rights['calculated_remaining_rights_sqm'] = total_areas
            remaining_rights['calculation_method'] = 'areas_found'
    
    # Method 5: Calculate comprehensive building rights dynamically
    if area and (floor_details or floor_percentages or relative_floor_percentages or building_coverage_percentages or roof_percentages or general_percentages):
        total_building_rights = 0
        floor_areas = {}
        
        # Calculate floor areas based on detailed floor information
        if floor_details:
            for floor_info in floor_details:
                floor_type = floor_info['type']
                percentage = floor_info['percentage']
                floor_area = area * (percentage / 100)
                floor_areas[floor_type] = floor_area
                total_building_rights += floor_area
                remaining_rights[f'{floor_type}_floor_area'] = int(floor_area)
        
        # Calculate relative floor areas (e.g., "75% מקומה טיפוסית")
        if relative_floor_percentages and floor_areas:
            for rel_info in relative_floor_percentages:
                percentage = rel_info['percentage']
                base_floor = rel_info['base_floor']
                if base_floor in floor_areas:
                    relative_area = floor_areas[base_floor] * (percentage / 100)
                    total_building_rights += relative_area
                    remaining_rights[f'relative_{base_floor}_{percentage}%_area'] = int(relative_area)
        
        # Calculate building coverage areas
        if building_coverage_percentages:
            for i, percentage in enumerate(building_coverage_percentages):
                coverage_area = area * (percentage / 100)
                total_building_rights += coverage_area
                remaining_rights[f'building_coverage_{i+1}_area'] = int(coverage_area)
        
        # Calculate roof areas
        if roof_percentages:
            for i, percentage in enumerate(roof_percentages):
                roof_area = area * (percentage / 100)
                total_building_rights += roof_area
                remaining_rights[f'roof_{i+1}_area'] = int(roof_area)
        
        # Calculate general percentages as building rights
        if general_percentages:
            for i, percentage in enumerate(general_percentages):
                general_area = area * (percentage / 100)
                total_building_rights += general_area
                remaining_rights[f'general_{i+1}_area'] = int(general_area)
        
        # Fallback to general percentages if no detailed floor info
        if not floor_details and floor_percentages:
            for i, percentage in enumerate(floor_percentages):
                floor_area = area * (percentage / 100)
                total_building_rights += floor_area
                remaining_rights[f'floor_{i+1}_area'] = int(floor_area)
        
        # Add other areas
        if basement_area:
            total_building_rights += basement_area
            remaining_rights['basement_area'] = basement_area
        if auxiliary_buildings:
            total_building_rights += auxiliary_buildings
            remaining_rights['auxiliary_buildings'] = auxiliary_buildings
        if service_percentage:
            service_area = area * (service_percentage / 100)
            total_building_rights += service_area
            remaining_rights['service_area'] = int(service_area)
        
        if total_building_rights > 0:
            remaining_rights['calculated_remaining_rights_sqm'] = int(total_building_rights)
            remaining_rights['calculation_method'] = 'comprehensive_building_rights'
            remaining_rights['total_building_rights'] = int(total_building_rights)
            remaining_rights['floor_details'] = floor_details
            remaining_rights['relative_floor_percentages'] = relative_floor_percentages
            remaining_rights['building_coverage_percentages'] = building_coverage_percentages
            remaining_rights['roof_percentages'] = roof_percentages
            remaining_rights['general_percentages'] = general_percentages
    
    return remaining_rights

def get_remaining_rights_sqm(parsed_data: Dict[str, Any], parcel_area_sqm: Optional[float] = None) -> Optional[int]:
    """
    Get the calculated remaining rights in square meters.
    
    Args:
        parsed_data: Parsed data from parse_zchuyot
        parcel_area_sqm: Parcel area in square meters (if known)
    
    Returns:
        Remaining rights in square meters, or None if cannot calculate
    """
    remaining_rights = calculate_remaining_rights_from_parsed_data(parsed_data, parcel_area_sqm)
    return remaining_rights.get('calculated_remaining_rights_sqm')
