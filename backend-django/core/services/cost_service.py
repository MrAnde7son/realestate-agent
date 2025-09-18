"""
Cost estimation service for building construction costs (Dekel-style estimates).
"""
import logging
from typing import Dict, Any, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class CostService:
    """Service for construction cost estimation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Base cost per sqm by region and quality
        self.base_costs = {
            "TA": {  # Tel Aviv
                "basic": 6000,
                "standard": 8000,
                "premium": 12000
            },
            "CENTER": {  # Center
                "basic": 5500,
                "standard": 7500,
                "premium": 11000
            },
            "NORTH": {  # North
                "basic": 5000,
                "standard": 7000,
                "premium": 10000
            },
            "SOUTH": {  # South
                "basic": 4500,
                "standard": 6500,
                "premium": 9500
            }
        }
        
        # Scope multipliers
        self.scope_multipliers = {
            "shell": 1.0,  # Basic structure
            "finish": 0.3,  # Interior finishing
            "electric_points": 0.1,  # Electrical outlets
            "plumbing_points": 0.15,  # Plumbing fixtures
            "kitchen_units": 0.2,  # Kitchen cabinets
            "balcony_m2": 0.4,  # Balcony construction
            "elevator_install": 0.3,  # Elevator installation
            "facade_upgrade": 0.25  # Facade improvements
        }
    
    def estimate_build_cost(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate building construction costs based on area, scope, region, and quality.
        
        Args:
            payload: Dictionary containing:
                - area_m2: Building area in square meters
                - scope: List of construction scopes
                - region: Region code (TA, CENTER, NORTH, SOUTH)
                - quality: Quality level (basic, standard, premium)
                
        Returns:
            Dict with cost breakdown and totals
        """
        try:
            area_m2 = payload.get("area_m2", 0)
            scope = payload.get("scope", ["shell"])
            region = payload.get("region", "CENTER")
            quality = payload.get("quality", "standard")
            
            if area_m2 <= 0:
                return self._empty_estimate()
            
            # Get base cost per sqm
            base_cost_per_sqm = self.base_costs.get(region, {}).get(quality, 6000)
            
            # Calculate costs for each scope
            breakdown = {}
            total_cost = 0
            
            for scope_item in scope:
                if scope_item in self.scope_multipliers:
                    multiplier = self.scope_multipliers[scope_item]
                    scope_cost = area_m2 * base_cost_per_sqm * multiplier
                    breakdown[scope_item] = {
                        "cost_per_sqm": base_cost_per_sqm * multiplier,
                        "total_cost": scope_cost,
                        "area_m2": area_m2
                    }
                    total_cost += scope_cost
            
            # Calculate Low/Base/High estimates
            low_multiplier = 0.85
            high_multiplier = 1.25
            
            low_total = total_cost * low_multiplier
            high_total = total_cost * high_multiplier
            
            # Add VAT (18%)
            vat_rate = 0.18
            total_with_vat = total_cost * (1 + vat_rate)
            low_with_vat = low_total * (1 + vat_rate)
            high_with_vat = high_total * (1 + vat_rate)
            
            return {
                "breakdown": breakdown,
                "totals": {
                    "base_cost": total_cost,
                    "base_cost_with_vat": total_with_vat,
                    "low_cost": low_total,
                    "low_cost_with_vat": low_with_vat,
                    "high_cost": high_total,
                    "high_cost_with_vat": high_with_vat
                },
                "metadata": {
                    "area_m2": area_m2,
                    "region": region,
                    "quality": quality,
                    "scope": scope,
                    "base_cost_per_sqm": base_cost_per_sqm,
                    "vat_rate": vat_rate
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating build cost: {e}")
            return self._empty_estimate()
    
    def _empty_estimate(self) -> Dict[str, Any]:
        """Return empty estimate structure."""
        return {
            "breakdown": {},
            "totals": {
                "base_cost": 0,
                "base_cost_with_vat": 0,
                "low_cost": 0,
                "low_cost_with_vat": 0,
                "high_cost": 0,
                "high_cost_with_vat": 0
            },
            "metadata": {
                "area_m2": 0,
                "region": "CENTER",
                "quality": "standard",
                "scope": [],
                "base_cost_per_sqm": 0,
                "vat_rate": 0.18
            }
        }
    
    def get_available_regions(self) -> List[Dict[str, str]]:
        """Get list of available regions."""
        return [
            {"code": "TA", "name": "תל אביב"},
            {"code": "CENTER", "name": "מרכז"},
            {"code": "NORTH", "name": "צפון"},
            {"code": "SOUTH", "name": "דרום"}
        ]
    
    def get_available_qualities(self) -> List[Dict[str, str]]:
        """Get list of available quality levels."""
        return [
            {"code": "basic", "name": "בסיסי"},
            {"code": "standard", "name": "סטנדרטי"},
            {"code": "premium", "name": "פרימיום"}
        ]
    
    def get_available_scopes(self) -> List[Dict[str, str]]:
        """Get list of available construction scopes."""
        return [
            {"code": "shell", "name": "שלד הבניין"},
            {"code": "finish", "name": "גימור פנימי"},
            {"code": "electric_points", "name": "נקודות חשמל"},
            {"code": "plumbing_points", "name": "נקודות אינסטלציה"},
            {"code": "kitchen_units", "name": "יחידות מטבח"},
            {"code": "balcony_m2", "name": "מרפסות"},
            {"code": "elevator_install", "name": "התקנת מעלית"},
            {"code": "facade_upgrade", "name": "שיפור חזית"}
        ]
