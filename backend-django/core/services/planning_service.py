"""
Planning service for calculating coverage, setbacks, and height analysis.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from django.db import transaction
from ..models import Asset, PlanningMetrics

logger = logging.getLogger(__name__)


class PlanningService:
    """Service for planning calculations and analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _calculate_polygon_area(self, geojson: Dict) -> float:
        """
        Simple polygon area calculation using the shoelace formula.
        This is a simplified implementation for development.
        """
        try:
            if geojson.get('type') == 'Polygon':
                coordinates = geojson['coordinates'][0]  # Exterior ring
                return self._shoelace_area(coordinates)
            elif geojson.get('type') == 'MultiPolygon':
                total_area = 0
                for polygon in geojson['coordinates']:
                    total_area += self._shoelace_area(polygon[0])  # Exterior ring
                return total_area
            return 0
        except Exception as e:
            self.logger.error(f"Error calculating polygon area: {e}")
            return 0
    
    def _shoelace_area(self, coordinates: List[List[float]]) -> float:
        """Calculate area using the shoelace formula (simplified for development)."""
        if len(coordinates) < 3:
            return 0
        
        # Simple approximation - in production use proper geodesic calculations
        area = 0
        n = len(coordinates)
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        return abs(area) / 2 * 111000 * 111000  # Rough conversion to square meters
    
    def compute_coverage(self, asset: Asset, parcel_geojson: Optional[Dict], footprint_geojson: Optional[Dict]) -> Dict[str, Any]:
        """
        Compute coverage percentage and area calculations.
        
        Args:
            asset: Asset instance
            parcel_geojson: GeoJSON polygon of parcel
            footprint_geojson: GeoJSON polygon of building footprint
            
        Returns:
            Dict with coverage calculations
        """
        try:
            parcel_area_m2 = None
            footprint_area_m2 = None
            coverage_pct = None
            confidence = "LOW"
            
            if parcel_geojson and footprint_geojson:
                try:
                    # Simple area calculation for GeoJSON polygons
                    # This is a simplified implementation - in production you'd use proper GIS libraries
                    parcel_area_m2 = self._calculate_polygon_area(parcel_geojson)
                    footprint_area_m2 = self._calculate_polygon_area(footprint_geojson)
                    
                    # Calculate coverage percentage
                    if parcel_area_m2 > 0:
                        coverage_pct = (footprint_area_m2 / parcel_area_m2) * 100
                        confidence = "HIGH"
                    else:
                        coverage_pct = 0
                        confidence = "LOW"
                        
                except Exception as e:
                    self.logger.error(f"Error calculating coverage for asset {asset.id}: {e}")
                    confidence = "LOW"
            
            return {
                "parcel_area_m2": parcel_area_m2,
                "footprint_area_m2": footprint_area_m2,
                "coverage_pct": coverage_pct,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error in compute_coverage for asset {asset.id}: {e}")
            return {
                "parcel_area_m2": None,
                "footprint_area_m2": None,
                "coverage_pct": None,
                "confidence": "LOW"
            }
    
    def validate_setbacks(self, asset: Asset, rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate building setbacks against planning rules.
        
        Args:
            asset: Asset instance
            rules: Dictionary with setback rules (e.g., {"front": 5, "side": 3, "rear": 4})
            
        Returns:
            Dict with setback validation results
        """
        try:
            violations = []
            confidence = "LOW"
            
            # This is a simplified implementation
            # In a real system, you would:
            # 1. Get the parcel boundary
            # 2. Get the building footprint
            # 3. Calculate setbacks for each side
            # 4. Compare against allowed setbacks
            
            # For now, return empty violations with low confidence
            # This would be implemented with actual GIS calculations
            
            return {
                "violations": violations,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error in validate_setbacks for asset {asset.id}: {e}")
            return {
                "violations": [],
                "confidence": "LOW"
            }
    
    def validate_height(self, asset: Asset, rules: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate building height against planning rules.
        
        Args:
            asset: Asset instance
            rules: Dictionary with height rules (e.g., {"max_floors": 4, "max_height_m": 12})
            current: Dictionary with current building data (e.g., {"floors": 3, "height_m": 9})
            
        Returns:
            Dict with height validation results
        """
        try:
            height_current = current or {}
            height_allowed = rules or {}
            height_delta = {}
            confidence = "LOW"
            
            # Calculate height differences
            if height_current.get("floors") and height_allowed.get("max_floors"):
                height_delta["delta_floors"] = height_current["floors"] - height_allowed["max_floors"]
            
            if height_current.get("height_m") and height_allowed.get("max_height_m"):
                height_delta["delta_m"] = height_current["height_m"] - height_allowed["max_height_m"]
            
            # Determine confidence based on data availability
            if height_current and height_allowed:
                confidence = "HIGH"
            elif height_current or height_allowed:
                confidence = "MEDIUM"
            
            return {
                "height_current": height_current,
                "height_allowed": height_allowed,
                "height_delta": height_delta,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error in validate_height for asset {asset.id}: {e}")
            return {
                "height_current": {},
                "height_allowed": {},
                "height_delta": {},
                "confidence": "LOW"
            }
    
    @transaction.atomic
    def compute_planning_metrics(self, asset: Asset, data: Dict[str, Any]) -> PlanningMetrics:
        """
        Compute and save planning metrics for an asset.
        
        Args:
            asset: Asset instance
            data: Dictionary with planning data including:
                - parcel: GeoJSON of parcel
                - footprint: GeoJSON of building footprint
                - rules: Planning rules
                - current: Current building data
                
        Returns:
            PlanningMetrics instance
        """
        try:
            # Compute coverage
            coverage_data = self.compute_coverage(
                asset, 
                data.get("parcel"), 
                data.get("footprint")
            )
            
            # Validate setbacks
            setback_data = self.validate_setbacks(
                asset, 
                data.get("rules", {}).get("setbacks", {})
            )
            
            # Validate height
            height_data = self.validate_height(
                asset, 
                data.get("rules", {}).get("height", {}),
                data.get("current", {})
            )
            
            # Determine overall confidence
            confidences = [
                coverage_data.get("confidence", "LOW"),
                setback_data.get("confidence", "LOW"),
                height_data.get("confidence", "LOW")
            ]
            
            if "HIGH" in confidences:
                overall_confidence = "HIGH"
            elif "MEDIUM" in confidences:
                overall_confidence = "MEDIUM"
            else:
                overall_confidence = "LOW"
            
            # Create or update PlanningMetrics
            planning_metrics, created = PlanningMetrics.objects.get_or_create(
                asset=asset,
                defaults={
                    "parcel_area_m2": coverage_data.get("parcel_area_m2"),
                    "footprint_area_m2": coverage_data.get("footprint_area_m2"),
                    "coverage_pct": coverage_data.get("coverage_pct"),
                    "allowed_envelope_polygon": data.get("parcel"),
                    "setback_violations": setback_data.get("violations", []),
                    "height_current": height_data.get("height_current", {}),
                    "height_allowed": height_data.get("height_allowed", {}),
                    "height_delta": height_data.get("height_delta", {}),
                    "calc_confidence": overall_confidence
                }
            )
            
            if not created:
                # Update existing metrics
                planning_metrics.parcel_area_m2 = coverage_data.get("parcel_area_m2")
                planning_metrics.footprint_area_m2 = coverage_data.get("footprint_area_m2")
                planning_metrics.coverage_pct = coverage_data.get("coverage_pct")
                planning_metrics.allowed_envelope_polygon = data.get("parcel")
                planning_metrics.setback_violations = setback_data.get("violations", [])
                planning_metrics.height_current = height_data.get("height_current", {})
                planning_metrics.height_allowed = height_data.get("height_allowed", {})
                planning_metrics.height_delta = height_data.get("height_delta", {})
                planning_metrics.calc_confidence = overall_confidence
                planning_metrics.save()
            
            self.logger.info(f"Planning metrics {'created' if created else 'updated'} for asset {asset.id}")
            return planning_metrics
            
        except Exception as e:
            self.logger.error(f"Error computing planning metrics for asset {asset.id}: {e}")
            raise
