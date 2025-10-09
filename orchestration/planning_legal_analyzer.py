#!/usr/bin/env python3
"""
Planning and Legal Analysis Calculator

This module calculates the four key planning and legal analysis fields:
1. Rights Usage Percentage (רמת ניצול זכויות)
2. Legal Restrictions (מגבלות משפטיות) 
3. Urban Renewal Potential (פוטנציאל התחדשות)
4. Betterment Levy (היטל השבחה צפוי)
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PlanningLegalAnalysis:
    """Container for planning and legal analysis results."""
    rights_usage_pct: Optional[float] = None
    legal_restrictions: Optional[str] = None
    urban_renewal_potential: Optional[str] = None
    betterment_levy: Optional[str] = None
    # Enhanced planning metrics
    building_coverage_pct: Optional[float] = None
    height_analysis: Optional[Dict[str, Any]] = None
    setback_analysis: Optional[Dict[str, Any]] = None


def calculate_planning_legal_analysis(asset, gis_data: Dict[str, Any], tabu_data: Dict[str, Any] = None) -> PlanningLegalAnalysis:
    """
    Calculate comprehensive planning and legal analysis for an asset.
    
    Args:
        asset: Asset instance
        gis_data: GIS collector data including permits, rights, plans
        tabu_data: Tabu data including mortgages and liens
        
    Returns:
        PlanningLegalAnalysis object with calculated values
    """
    analysis = PlanningLegalAnalysis()
    
    # Calculate rights usage percentage
    analysis.rights_usage_pct = _calculate_rights_usage_percentage(asset, gis_data)
    
    # Calculate legal restrictions
    analysis.legal_restrictions = _calculate_legal_restrictions(asset, gis_data, tabu_data)
    
    # Calculate urban renewal potential
    analysis.urban_renewal_potential = _calculate_urban_renewal_potential(asset, gis_data)
    
    # Calculate betterment levy
    analysis.betterment_levy = _calculate_betterment_levy(asset, gis_data)
    
    # Calculate enhanced planning metrics
    analysis.building_coverage_pct = _calculate_building_coverage(asset, gis_data)
    analysis.height_analysis = _calculate_height_analysis(asset, gis_data)
    analysis.setback_analysis = _calculate_setback_analysis(asset, gis_data)
    
    return analysis


def _calculate_rights_usage_percentage(asset, gis_data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate the percentage of building rights utilization.
    
    This is calculated as: (Current Building Area / Maximum Allowed Building Area) * 100
    """
    try:
        # Get parcel area for calculations
        parcel_area = asset.parcel_area or gis_data.get('parcel_area')
        if not parcel_area:
            return None
            
        # Get current building area from permits
        current_building_area = 0
        permits = gis_data.get('permits', [])
        
        for permit in permits:
            if isinstance(permit, dict):
                # Sum up all building areas from permits
                residential_area = float(permit.get('permit_residential_area', 0) or 0)
                commercial_area = float(permit.get('permit_commercial_area', 0) or 0)
                public_area = float(permit.get('permit_public_area', 0) or 0)
                parking_area = float(permit.get('permit_parking_area', 0) or 0)
                
                current_building_area += residential_area + commercial_area + public_area + parking_area
        
        # If no permits, try to estimate from existing building
        if current_building_area == 0 and asset.total_area:
            current_building_area = asset.total_area
            
        # Get maximum allowed building area from rights data
        max_building_area = _get_maximum_building_area(gis_data, parcel_area)
        
        if max_building_area and max_building_area > 0:
            usage_pct = (current_building_area / max_building_area) * 100
            return round(min(usage_pct, 100), 1)  # Cap at 100%
            
    except (ValueError, TypeError, ZeroDivisionError):
        pass
        
    return None


def _get_maximum_building_area(gis_data: Dict[str, Any], parcel_area: float) -> Optional[float]:
    """Get maximum allowed building area from rights data."""
    try:
        # Check privilege page data first
        privilege_data_list = gis_data.get('privilege_page_data', [])
        if privilege_data_list:
            # Handle both old single dict format and new list format
            privilege_data = privilege_data_list[0] if isinstance(privilege_data_list, list) else privilege_data_list
            
            if isinstance(privilege_data, dict):
                rights = privilege_data.get('rights', {})
                
                # Try to get building percentage
                percent_building = rights.get('percent_building')
                if percent_building and parcel_area:
                    return (percent_building / 100) * parcel_area
                
                # Try to get specific building rights areas
                building_rights_areas = rights.get('building_rights_areas', [])
                if building_rights_areas:
                    return sum(building_rights_areas)
        
        # Check GIS rights data
        rights = gis_data.get('rights', [])
        if rights and isinstance(rights, list) and len(rights) > 0:
            right = rights[0]
            if isinstance(right, dict):
                # Look for building coverage percentage
                building_coverage = right.get('building_coverage_percentages', [])
                if building_coverage and parcel_area:
                    max_coverage = max(building_coverage)
                    return (max_coverage / 100) * parcel_area
        
        # Default assumption: 80% building coverage
        return parcel_area * 0.8
        
    except (ValueError, TypeError):
        return None


def _calculate_legal_restrictions(asset, gis_data: Dict[str, Any], tabu_data: Dict[str, Any] = None) -> Optional[str]:
    """
    Calculate legal restrictions based on permits, plans, and tabu data.
    """
    restrictions = []
    
    try:
        # Check for permit restrictions
        permits = gis_data.get('permits', [])
        for permit in permits:
            if isinstance(permit, dict):
                # Check for specific restrictions
                permit_type = permit.get('permit_subject_type', '')
                process = permit.get('permit_process', '')
                
                if 'הגבלה' in permit_type or 'הגבלה' in process:
                    restrictions.append('הגבלות בהיתר בנייה')
                
                # Check for rights notification requirement
                if permit.get('permit_rights_notification'):
                    restrictions.append('הודעה על זכויות נדרשת')
        
        # Check for plan restrictions
        plans = gis_data.get('plans', [])
        for plan in plans:
            if isinstance(plan, dict):
                plan_status = plan.get('status', '')
                if 'הגבלה' in plan_status or 'הגבלה' in plan.get('description', ''):
                    restrictions.append('הגבלות בתוכנית')
        
        # Check tabu data for mortgages and liens
        if tabu_data:
            mortgages = tabu_data.get('mortgages', [])
            liens = tabu_data.get('liens', [])
            
            if mortgages:
                restrictions.append(f'שעבודים לטובת בנק ({len(mortgages)} שעבודים)')
            
            if liens:
                restrictions.append(f'הערות אזהרה ({len(liens)} הערות)')
        
        # Check privilege page for alerts
        privilege_data_list = gis_data.get('privilege_page_data', [])
        if privilege_data_list:
            privilege_data = privilege_data_list[0] if isinstance(privilege_data_list, list) else privilege_data_list
            if isinstance(privilege_data, dict):
                alerts = privilege_data.get('alerts', [])
                if alerts:
                    restrictions.append(f'הערות אזהרה בקרקע ({len(alerts)} הערות)')
        
        if restrictions:
            return '; '.join(restrictions)
            
    except (ValueError, TypeError):
        pass
        
    return None


def _calculate_urban_renewal_potential(asset, gis_data: Dict[str, Any]) -> Optional[str]:
    """
    Calculate urban renewal potential based on permits, plans, and building age.
    """
    try:
        # Check for urban renewal permits
        permits = gis_data.get('permits', [])
        urban_renewal_permits = []
        
        for permit in permits:
            if isinstance(permit, dict):
                # Check if permit is for urban renewal
                if permit.get('permit_urban_renewal'):
                    urban_renewal_permits.append(permit)
                
                # Check permit type for urban renewal keywords
                permit_type = permit.get('permit_subject_type', '')
                if any(keyword in permit_type.lower() for keyword in ['תמ"א', 'חידוש', 'פינוי', 'בינוי']):
                    urban_renewal_permits.append(permit)
        
        if urban_renewal_permits:
            return f'תמ"א 38/2 - {len(urban_renewal_permits)} היתרים'
        
        # Check building age for renewal potential
        if asset.year_built:
            building_age = 2024 - asset.year_built  # Current year approximation
            if building_age > 30:
                return 'פוטנציאל תמ"א 38/2 (בניין ישן)'
            elif building_age > 20:
                return 'פוטנציאל חידוש עירוני (בניין בינוני)'
        
        # Check for nearby urban renewal projects
        plans = gis_data.get('plans', [])
        urban_renewal_plans = []
        
        for plan in plans:
            if isinstance(plan, dict):
                plan_description = plan.get('description', '')
                if any(keyword in plan_description.lower() for keyword in ['תמ"א', 'חידוש', 'פינוי', 'בינוי']):
                    urban_renewal_plans.append(plan)
        
        if urban_renewal_plans:
            return f'תוכניות חידוש עירוני באזור ({len(urban_renewal_plans)} תוכניות)'
        
    except (ValueError, TypeError):
        pass
        
    return None


def _calculate_betterment_levy(asset, gis_data: Dict[str, Any]) -> Optional[str]:
    """
    Calculate expected betterment levy based on building rights and zoning.
    """
    try:
        # Get parcel area
        parcel_area = asset.parcel_area or gis_data.get('parcel_area')
        if not parcel_area:
            return None
        
        # Get maximum building rights
        max_building_area = _get_maximum_building_area(gis_data, parcel_area)
        if not max_building_area:
            return None
        
        # Get current building area
        current_building_area = asset.total_area or 0
        
        # Calculate unused rights
        unused_rights = max_building_area - current_building_area
        if unused_rights <= 0:
            return 'אין היטל השבחה (ניצול מלא)'
        
        # Estimate betterment levy based on unused rights and location
        # Rough estimation: 1000-3000 NIS per sqm depending on location
        base_rate = 1500  # Base rate per sqm
        
        # Adjust rate based on city
        if asset.city:
            if any(city in asset.city for city in ['תל אביב', 'רמת גן', 'הרצליה']):
                base_rate = 3000  # High-value areas
            elif any(city in asset.city for city in ['פתח תקווה', 'ראשון לציון', 'חולון']):
                base_rate = 2000  # Medium-value areas
            else:
                base_rate = 1000  # Lower-value areas
        
        # Calculate estimated levy
        estimated_levy = int(unused_rights * base_rate)
        
        # Format the result
        if estimated_levy >= 1000000:
            return f'היטל צפוי כ-{estimated_levy // 1000000} מיליון ₪'
        elif estimated_levy >= 1000:
            return f'היטל צפוי כ-{estimated_levy // 1000} אלף ₪'
        else:
            return f'היטל צפוי כ-{estimated_levy} ₪'
            
    except (ValueError, TypeError):
        pass
        
    return None


def apply_planning_legal_analysis_to_asset(asset, analysis: PlanningLegalAnalysis):
    """
    Apply the calculated planning and legal analysis to an asset.
    
    Args:
        asset: Asset instance to update
        analysis: PlanningLegalAnalysis object with calculated values
    """
    if analysis.rights_usage_pct is not None:
        asset.rights_usage_pct = analysis.rights_usage_pct
        
    if analysis.legal_restrictions:
        asset.legal_restrictions = analysis.legal_restrictions
        
    if analysis.urban_renewal_potential:
        asset.urban_renewal_potential = analysis.urban_renewal_potential
        
    if analysis.betterment_levy:
        asset.betterment_levy = analysis.betterment_levy
        
    if analysis.building_coverage_pct is not None:
        asset.building_coverage_pct = analysis.building_coverage_pct
        
    if analysis.height_analysis:
        asset.height_analysis = analysis.height_analysis
        
    if analysis.setback_analysis:
        asset.setback_analysis = analysis.setback_analysis


def _calculate_building_coverage(asset, gis_data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate building coverage percentage based on permit data and parcel area.
    
    Coverage = (Total Building Area / Parcel Area) * 100
    """
    try:
        # Get parcel area
        parcel_area = asset.parcel_area
        if not parcel_area:
            return None
            
        # Calculate total building area from permits
        total_building_area = 0
        permits = gis_data.get('permits', [])
        
        for permit in permits:
            if isinstance(permit, dict):
                # Sum all building areas from permits
                residential_area = float(permit.get('permit_residential_area', 0) or 0)
                commercial_area = float(permit.get('permit_commercial_area', 0) or 0)
                public_area = float(permit.get('permit_public_area', 0) or 0)
                parking_area = float(permit.get('permit_parking_area', 0) or 0)
                
                total_building_area += residential_area + commercial_area + public_area + parking_area
        
        # If no permits, try to estimate from existing building
        if total_building_area == 0 and asset.total_area:
            total_building_area = asset.total_area
            
        # Calculate coverage percentage
        if parcel_area > 0 and total_building_area > 0:
            coverage_pct = (total_building_area / parcel_area) * 100
            return round(min(coverage_pct, 100), 1)  # Cap at 100%
            
    except (ValueError, TypeError, ZeroDivisionError):
        pass
        
    return None


def _calculate_height_analysis(asset, gis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calculate height analysis including current vs allowed height/floors.
    """
    try:
        height_analysis = {
            'current_floors': None,
            'current_height_m': None,
            'allowed_floors': None,
            'allowed_height_m': None,
            'height_compliance': 'unknown',
            'confidence': 'low'
        }
        
        # Get current building data
        current_floors = asset.total_floors
        if current_floors:
            height_analysis['current_floors'] = current_floors
            # Estimate height: assume 3 meters per floor
            height_analysis['current_height_m'] = current_floors * 3
        
        # Get height data from permits
        permits = gis_data.get('permits', [])
        permit_floors = []
        
        for permit in permits:
            if isinstance(permit, dict):
                housing_units = permit.get('permit_housing_units')
                if housing_units:
                    # Estimate floors from housing units (rough approximation)
                    estimated_floors = max(1, housing_units // 2)  # Assume 2 units per floor
                    permit_floors.append(estimated_floors)
        
        if permit_floors:
            max_permit_floors = max(permit_floors)
            if not current_floors or max_permit_floors > current_floors:
                height_analysis['current_floors'] = max_permit_floors
                height_analysis['current_height_m'] = max_permit_floors * 3
        
        # Get allowed height from rights data
        rights = gis_data.get('rights', [])
        if rights and isinstance(rights, list) and len(rights) > 0:
            right = rights[0]
            if isinstance(right, dict):
                # Look for height restrictions in rights data
                # This would need to be parsed from Hebrew text in real implementation
                pass
        
        # Get allowed height from privilege page data
        privilege_data_list = gis_data.get('privilege_page_data', [])
        if privilege_data_list:
            privilege_data = privilege_data_list[0] if isinstance(privilege_data_list, list) else privilege_data_list
            if isinstance(privilege_data, dict):
                rights = privilege_data.get('rights', {})
                number_of_floors = rights.get('number_of_floors')
                if number_of_floors:
                    height_analysis['allowed_floors'] = number_of_floors
                    height_analysis['allowed_height_m'] = number_of_floors * 3
        
        # Determine compliance
        if height_analysis['current_floors'] and height_analysis['allowed_floors']:
            if height_analysis['current_floors'] <= height_analysis['allowed_floors']:
                height_analysis['height_compliance'] = 'compliant'
            else:
                height_analysis['height_compliance'] = 'non_compliant'
            height_analysis['confidence'] = 'high'
        elif height_analysis['current_floors'] or height_analysis['allowed_floors']:
            height_analysis['confidence'] = 'medium'
        
        return height_analysis
        
    except (ValueError, TypeError):
        pass
        
    return None


def _calculate_setback_analysis(asset, gis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calculate setback analysis based on building footprint and parcel boundaries.
    This is a simplified implementation - in production you'd use proper GIS calculations.
    """
    try:
        setback_analysis = {
            'violations': [],
            'front_setback': None,
            'side_setback': None,
            'rear_setback': None,
            'confidence': 'low'
        }
        
        # Get parcel and building data
        parcel_area = asset.parcel_area
        building_area = asset.total_area or asset.area
        
        if parcel_area and building_area:
            # Simple setback estimation based on area ratios
            # This is a very rough approximation
            coverage_ratio = building_area / parcel_area
            
            if coverage_ratio > 0.8:
                setback_analysis['violations'].append('ניצול גבוה - חסרים שטחי נסיגה')
                setback_analysis['confidence'] = 'medium'
            elif coverage_ratio > 0.6:
                setback_analysis['violations'].append('ניצול בינוני - בדיקת נסיגות נדרשת')
                setback_analysis['confidence'] = 'low'
            else:
                setback_analysis['confidence'] = 'low'
        
        # Check for specific setback requirements in permits
        permits = gis_data.get('permits', [])
        for permit in permits:
            if isinstance(permit, dict):
                # Look for setback-related information in permit data
                permit_type = permit.get('permit_subject_type', '')
                if 'נסיגה' in permit_type or 'setback' in permit_type.lower():
                    setback_analysis['violations'].append('הגבלות נסיגה בהיתר')
                    setback_analysis['confidence'] = 'high'
        
        return setback_analysis
        
    except (ValueError, TypeError):
        pass
        
    return None
