"""
Yad2 Real Estate Search Helper
Provides unified search functions with automatic parameter resolution
"""

from typing import Dict, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Yad2SearchHelper:
    """Helper class for Yad2 real estate searches with automatic parameter resolution"""
    
    # Cache for property types and locations to avoid repeated API calls
    _property_types_cache: Optional[Dict] = None
    _locations_cache: Dict = {}
    
    @classmethod
    def get_property_type_code(cls, property_name: str) -> Optional[int]:
        """
        Get property type code by name (Hebrew or English)
        
        Args:
            property_name: Property type name in Hebrew or English
            
        Returns:
            Property type code or None if not found
        """
        try:
            # Use existing PropertyTypeUtils first
            from .utils.property_types import PropertyTypeUtils
            
            # Try Hebrew name first
            code = PropertyTypeUtils.hebrew_name_to_code(property_name)
            if code:
                logger.info(f"Found property type '{property_name}' with code: {code} (Hebrew)")
                return code
            
            # Try English name
            code = PropertyTypeUtils.english_name_to_code(property_name)
            if code:
                logger.info(f"Found property type '{property_name}' with code: {code} (English)")
                return code
            
            # Fallback to MCP server if not found in existing utils
            from .mcp.server import search_property_types
            
            result = search_property_types(search_term=property_name)
            if result.get('success') and result.get('exact_matches'):
                # Get the first exact match
                code = list(result['exact_matches'].keys())[0]
                logger.info(f"Found property type '{property_name}' with code: {code} (MCP)")
                return int(code)
            
            # If no exact match, try to find similar
            if result.get('total_found', 0) > 0:
                logger.warning(f"No exact match for '{property_name}', but found {result['total_found']} similar results")
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting property type code for '{property_name}': {e}")
            return None
    
    @classmethod
    def get_location_codes(cls, city_name: str, neighborhood_name: Optional[str] = None) -> Dict[str, int]:
        """
        Get location codes for city and optionally neighborhood
        
        Args:
            city_name: City name
            neighborhood_name: Optional neighborhood name
            
        Returns:
            Dict with city_id and optionally neighborhood_id
        """
        try:
            # Import here to avoid circular imports
            from .mcp.server import search_locations
            
            result = search_locations(search_text=city_name)
            if not result.get('success'):
                logger.error(f"Failed to search for city: {city_name}")
                return {}
            
            location_codes = {}
            
            # Get city code
            cities = result.get('cities', [])
            if cities:
                city_id = int(cities[0]['cityId'])
                location_codes['city_id'] = city_id
                logger.info(f"Found city '{city_name}' with ID: {city_id}")
            else:
                logger.error(f"City '{city_name}' not found")
                return {}
            
            # Get neighborhood code if specified
            if neighborhood_name:
                hoods = result.get('hoods', [])
                for hood in hoods:
                    if neighborhood_name.lower() in hood['fullTitleText'].lower():
                        hood_id = int(hood['hoodId'])
                        location_codes['neighborhood_id'] = hood_id
                        logger.info(f"Found neighborhood '{neighborhood_name}' with ID: {hood_id}")
                        break
                else:
                    logger.warning(f"Neighborhood '{neighborhood_name}' not found in city '{city_name}'")
            
            return location_codes
            
        except Exception as e:
            logger.error(f"Error getting location codes for '{city_name}': {e}")
            return {}
    
    @classmethod
    def search_real_estate_smart(
        cls,
        property_type: str,
        city: str,
        neighborhood: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Smart search for real estate with automatic parameter resolution
        
        Args:
            property_type: Property type name (Hebrew or English)
            city: City name
            neighborhood: Optional neighborhood name
            **kwargs: Additional search parameters (price, rooms, etc.)
            
        Returns:
            Search results dictionary
        """
        try:
            # Import here to avoid circular imports
            from .mcp.server import search_real_estate
            
            logger.info(f"Starting smart search: {property_type} in {city}" + 
                       (f", {neighborhood}" if neighborhood else ""))
            
            # Get property type code
            property_code = cls.get_property_type_code(property_type)
            if not property_code:
                raise ValueError(f"Property type '{property_type}' not found")
            
            # Get location codes
            location_codes = cls.get_location_codes(city, neighborhood)
            if not location_codes:
                raise ValueError(f"Location '{city}' not found")
            
            # Prepare search parameters
            search_params = {
                'property': property_code,
                'city': location_codes['city_id'],
                **kwargs
            }
            
            # Add neighborhood if found
            if 'neighborhood_id' in location_codes:
                search_params['neighborhood'] = location_codes['neighborhood_id']
            
            logger.info(f"Search parameters: {search_params}")
            
            # Perform search
            result = search_real_estate(**search_params)
            
            if result.get('success'):
                logger.info(f"Search successful: {result.get('total_assets', 0)} assets found")
            else:
                logger.error("Search failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in smart search: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def get_search_url(cls, **params) -> str:
        """
        Build search URL for the given parameters
        
        Args:
            **params: Search parameters
            
        Returns:
            Search URL string
        """
        try:
            # Import here to avoid circular imports
            from .mcp.server import build_search_url
            
            result = build_search_url(**params)
            return result.get('url', '')
            
        except Exception as e:
            logger.error(f"Error building search URL: {e}")
            return ""

# Convenience functions for common searches
def search_houses_in_neighborhood(neighborhood: str, city: str, **kwargs) -> Dict:
    """
    Search for properties in a specific neighborhood
    
    Args:
        neighborhood: Neighborhood name
        city: City name
        **kwargs: Additional search parameters (price, rooms, etc.)
    
    Returns:
        Search results dictionary
    """
    # This function is a wrapper for the MCP tool
    # It should be called through the MCP server, not directly
    return {
        'success': False, 
        'error': 'This function should be called through the MCP server. Use search_real_estate tool directly.',
        'mcp_tool': 'search_real_estate',
        'suggested_params': {
            'city': city,
            'neighborhood': neighborhood,
            **kwargs
        }
    }

def search_apartments_in_city(city: str, **kwargs) -> Dict:
    """Search for apartments in a specific city"""
    return Yad2SearchHelper.search_real_estate_smart(
        property_type="דירה",  # Using Hebrew name for code 1
        city=city,
        **kwargs
    )

def search_property_by_type_and_location(property_type: str, city: str, neighborhood: str = None, **kwargs) -> Dict:
    """Generic search function"""
    return Yad2SearchHelper.search_real_estate_smart(
        property_type=property_type,
        city=city,
        neighborhood=neighborhood,
        **kwargs
    )
