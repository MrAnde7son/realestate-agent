#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper

Enhanced Yad2 scraper with dynamic parameter support and comprehensive data extraction.
"""

import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..core import Yad2SearchParameters, Yad2ParameterReference, RealEstateListing, URLUtils


class Yad2Scraper:
    """Enhanced Yad2 scraper with dynamic parameter support."""
    
    def __init__(self, search_params=None, headers=None):
        """
        Initialize the scraper.
        
        Args:
            search_params: Yad2SearchParameters object or dict of parameters
            headers: Custom headers for requests
        """
        self.base_url = "https://www.yad2.co.il"
        self.search_endpoint = "/realestate/forsale"
        self.api_base_url = "https://gw.yad2.co.il"
        
        # Default headers to mimic a real browser
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": "https://www.yad2.co.il/"
        }
        # Initialize search parameters
        if isinstance(search_params, dict):
            self.search_params = Yad2SearchParameters(**search_params)
        elif isinstance(search_params, Yad2SearchParameters):
            self.search_params = search_params
        else:
            self.search_params = Yad2SearchParameters()
        
        self.listings = []
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Parameter reference for validation
        self.param_reference = Yad2ParameterReference()
    
    def fetch_property_types(self):
        """
        Fetch all available property types from Yad2 API.
        
        Returns:
            Dict containing property type information or None if failed
        """
        try:
            # API endpoint for property types (this might need to be discovered)
            # For now, we'll use the existing parameter reference
            property_types = self.param_reference.get_property_types()
            
            # Try to fetch from API if available
            try:
                # This is a placeholder - the actual endpoint needs to be discovered
                # response = self.session.get(f"{self.api_base_url}/property-types")
                # if response.status_code == 200:
                #     return response.json()
                pass
            except:
                pass
            
            # Return the static reference data
            return {
                'source': 'parameter_reference',
                'property_types': property_types,
                'total_count': len(property_types)
            }
            
        except Exception as e:
            print(f"Error fetching property types: {e}")
            return None
    
    def fetch_location_data(self, search_text):
        """
        Fetch location data from Yad2 address autocomplete API.
        
        Args:
            search_text: Text to search for (e.g., "רמת", "תל אביב")
            
        Returns:
            Dict containing location data or None if failed
        """
        try:
            url = f"{self.api_base_url}/address-autocomplete/realestate/v2"
            params = {'text': search_text}
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'search_text': search_text,
                    'hoods': data.get('hoods', []),
                    'cities': data.get('cities', []),
                    'areas': data.get('areas', []),
                    'top_areas': data.get('topAreas', []),
                    'streets': data.get('streets', [])
                }
            else:
                print(f"Failed to fetch location data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching location data: {e}")
            return None
    
    def get_all_property_type_codes(self):
        """
        Get all property type codes with descriptions.
        
        Returns:
            Dict mapping property type codes to descriptions
        """
        property_types = self.fetch_property_types()
        if property_types and 'property_types' in property_types:
            return property_types['property_types']
        return {}
    
    def search_property_types(self, search_term=None):
        """
        Search property types by name or get all if no search term.
        
        Args:
            search_term: Optional search term to filter property types
            
        Returns:
            Dict of matching property types
        """
        all_types = self.get_all_property_type_codes()
        
        if not search_term:
            return all_types
        
        # Filter by search term (case-insensitive)
        search_term_lower = search_term.lower()
        filtered_types = {}
        
        for code, name in all_types.items():
            if search_term_lower in name.lower():
                filtered_types[code] = name
        
        return filtered_types
    
    def get_property_type_by_code(self, code):
        """
        Get property type name by code.
        
        Args:
            code: Property type code
            
        Returns:
            Property type name or None if not found
        """
        all_types = self.get_all_property_type_codes()
        return all_types.get(int(code)) if code else None
    
    def get_property_type_codes_by_name(self, name):
        """
        Get property type codes by name (partial match).
        
        Args:
            name: Property type name or partial name
            
        Returns:
            List of matching codes
        """
        all_types = self.get_all_property_type_codes()
        matching_codes = []
        
        name_lower = name.lower()
        for code, type_name in all_types.items():
            if name_lower in type_name.lower():
                matching_codes.append(code)
        
        return matching_codes
    
    def get_all_location_codes(self):
        """
        Get comprehensive location information including cities, areas, and neighborhoods.
        
        Returns:
            Dict containing all location codes organized by type
        """
        # This would ideally fetch from Yad2 API, but for now we'll use the parameter reference
        # and provide a structure for future API integration
        
        location_data = {
            'top_areas': {
                1: 'North',
                2: 'Center', 
                3: 'South',
                4: 'Jerusalem Area',
                5: 'West Bank'
            },
            'areas': {
                1: 'Tel Aviv',
                3: 'Ramat Gan, Givatayim',
                18: 'Ramat Hasharon, Herzliya',
                51: 'Ramla - Lod',
                87: 'Ramot Menashe',
                97: 'Ramot Menashe'
            },
            'cities': {
                5000: 'Tel Aviv',
                6200: 'Jerusalem',
                6300: 'Haifa',
                8600: 'Ramat Gan',
                2650: 'Ramat Hasharon',
                8500: 'Ramla',
                122: 'Ramat Yishai'
            },
            'neighborhoods': {
                203: 'Ramat HaHayal',
                199: 'City Center',
                200: 'Neve Tzedek',
                312: 'Florentin',
                521: 'Ramot, Jerusalem'
            }
        }
        
        return location_data
    
    def search_locations(self, search_term):
        """
        Search for locations by name using the address autocomplete API.
        
        Args:
            search_term: Text to search for (e.g., "רמת", "תל אביב", "ירושלים")
            
        Returns:
            Dict containing matching locations organized by type
        """
        location_data = self.fetch_location_data(search_term)
        if not location_data:
            return {}
        
        # Organize the results
        results = {
            'search_term': search_term,
            'hoods': location_data.get('hoods', []),
            'cities': location_data.get('cities', []),
            'areas': location_data.get('areas', []),
            'top_areas': location_data.get('top_areas', []),
            'streets': location_data.get('streets', [])
        }
        
        return results
    
    def get_city_by_id(self, city_id):
        """
        Get city information by ID.
        
        Args:
            city_id: City ID
            
        Returns:
            Dict containing city information or None if not found
        """
        # Try to find in our reference data first
        location_data = self.get_all_location_codes()
        city_name = location_data['cities'].get(int(city_id))
        
        if city_name:
            return {
                'city_id': city_id,
                'name': city_name,
                'source': 'reference'
            }
        
        # If not found in reference, try to search by ID
        try:
            # This is a placeholder for future API integration
            # response = self.session.get(f"{self.api_base_url}/cities/{city_id}")
            # if response.status_code == 200:
            #     return response.json()
            pass
        except:
            pass
        
        return None
    
    def get_area_by_id(self, area_id):
        """
        Get area information by ID.
        
        Args:
            area_id: Area ID
            
        Returns:
            Dict containing area information or None if not found
        """
        location_data = self.get_all_location_codes()
        area_name = location_data['areas'].get(int(area_id))
        
        if area_name:
            return {
                'area_id': area_id,
                'name': area_name,
                'source': 'reference'
            }
        
        return None
    
    def get_neighborhood_by_id(self, neighborhood_id):
        """
        Get neighborhood information by ID.
        
        Args:
            neighborhood_id: Neighborhood ID
            
        Returns:
            Dict containing neighborhood information or None if not found
        """
        location_data = self.get_all_location_codes()
        neighborhood_name = location_data['neighborhoods'].get(int(neighborhood_id))
        
        if neighborhood_name:
            return {
                'neighborhood_id': neighborhood_id,
                'name': neighborhood_name,
                'source': 'reference'
            }
        
        return None
    
    def get_deal_types(self):
        """
        Get all available deal types (sale/rent).
        
        Returns:
            Dict containing deal type information
        """
        deal_types = {
            'sale': {
                'id': 'sale',
                'name': 'מכירה',
                'english_name': 'Sale',
                'description': 'Properties for sale'
            },
            'rent': {
                'id': 'rent', 
                'name': 'השכרה',
                'english_name': 'Rent',
                'description': 'Properties for rent'
            }
        }
        
        return deal_types
    
    def get_sale_types(self):
        """
        Get all available sale types.
        
        Returns:
            Dict containing sale type information
        """
        sale_types = {
            'regular': {
                'id': 'regular',
                'name': 'מכירה רגילה',
                'english_name': 'Regular Sale',
                'description': 'Standard property sale'
            },
            'new': {
                'id': 'new',
                'name': 'דירה חדשה',
                'english_name': 'New Property',
                'description': 'New construction properties'
            },
            'investment': {
                'id': 'investment',
                'name': 'השקעה',
                'english_name': 'Investment',
                'description': 'Investment properties'
            }
        }
        
        return sale_types
    
    def get_all_codes_summary(self):
        """
        Get a comprehensive summary of all available codes and their meanings.
        
        Returns:
            Dict containing all codes organized by category
        """
        summary = {
            'property_types': self.get_all_property_type_codes(),
            'locations': self.get_all_location_codes(),
            'deal_types': self.get_deal_types(),
            'sale_types': self.get_sale_types(),
            'features': {
                'elevator': {0: 'No', 1: 'Yes'},
                'balcony': {0: 'No', 1: 'Yes'},
                'renovated': {0: 'No', 1: 'Yes'},
                'accessibility': {0: 'No', 1: 'Yes'},
                'airCondition': {0: 'No', 1: 'Yes'},
                'bars': {0: 'No', 1: 'Yes'},
                'mamad': {0: 'No', 1: 'Yes'},
                'storage': {0: 'No', 1: 'Yes'},
                'terrace': {0: 'No', 1: 'Yes'},
                'garden': {0: 'No', 1: 'Yes'},
                'pets': {0: 'No', 1: 'Yes'},
                'furniture': {0: 'No', 1: 'Yes'}
            },
            'sort_orders': {
                'date': 'By date (newest first)',
                'price_asc': 'Price low to high',
                'price_desc': 'Price high to low',
                'size_asc': 'Size small to large',
                'size_desc': 'Size large to small'
            }
        }
        
        return summary
    
    def fetch_external_property_types(self):
        """
        Attempt to fetch property types from external sources or APIs.
        This is a placeholder for future integration with other real estate data providers.
        
        Returns:
            Dict containing external property type data or None if not available
        """
        external_sources = {
            'madlan': {
                'url': 'https://www.madlan.co.il/api/property-types',
                'description': 'Madlan property types API'
            },
            'homeless': {
                'url': 'https://www.homeless.co.il/api/property-types', 
                'description': 'Homeless property types API'
            }
        }
        
        # This is a placeholder for future implementation
        # In the future, this could make actual API calls to external sources
        return {
            'available_sources': external_sources,
            'status': 'not_implemented',
            'message': 'External API integration not yet implemented'
        }
    
    def export_codes_to_json(self, filename=None):
        """
        Export all codes and their meanings to a JSON file.
        
        Args:
            filename: Optional filename, defaults to timestamped filename
            
        Returns:
            Filename where codes were saved
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yad2_codes_{timestamp}.json"
        
        codes_data = {
            'export_time': datetime.now().isoformat(),
            'source': 'Yad2Scraper',
            'codes': self.get_all_codes_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(codes_data, f, ensure_ascii=False, indent=2)
        
        print(f"Exported all codes to {filename}")
        return filename
    
    def print_codes_summary(self):
        """
        Print a formatted summary of all available codes to console.
        """
        summary = self.get_all_codes_summary()
        
        print("=" * 60)
        print("YAD2 CODES SUMMARY")
        print("=" * 60)
        
        # Property Types
        print("\n📋 PROPERTY TYPES:")
        for code, name in summary['property_types'].items():
            print(f"  {code:2d}: {name}")
        
        # Top Areas
        print("\n🌍 TOP AREAS:")
        for code, name in summary['locations']['top_areas'].items():
            print(f"  {code}: {name}")
        
        # Cities
        print("\n🏙️  CITIES:")
        for code, name in summary['locations']['cities'].items():
            print(f"  {code}: {name}")
        
        # Deal Types
        print("\n💰 DEAL TYPES:")
        for deal_id, deal_info in summary['deal_types'].items():
            print(f"  {deal_id}: {deal_info['name']} ({deal_info['english_name']})")
        
        # Features
        print("\n🏠 FEATURES:")
        for feature, values in summary['features'].items():
            print(f"  {feature}: {values}")
        
        print("\n" + "=" * 60)
    
    def fetch_yad2_property_types_api(self):
        """
        Attempt to fetch property types from Yad2's internal API.
        This method tries to discover and use Yad2's actual property type endpoints.
        
        Returns:
            Dict containing property type data from Yad2 API or None if failed
        """
        possible_endpoints = [
            f"{self.api_base_url}/property-types",
            f"{self.api_base_url}/realestate/property-types",
            f"{self.api_base_url}/api/property-types",
            f"{self.api_base_url}/v1/property-types"
        ]
        
        for endpoint in possible_endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'source': 'yad2_api',
                        'endpoint': endpoint,
                        'data': data
                    }
            except Exception as e:
                continue
        
        return None
    
    def get_property_type_details(self, property_type_code):
        """
        Get detailed information about a specific property type.
        
        Args:
            property_type_code: Property type code
            
        Returns:
            Dict containing detailed property type information
        """
        property_types = self.get_all_property_type_codes()
        property_name = property_types.get(int(property_type_code))
        
        if not property_name:
            return None
        
        # Basic property type information
        details = {
            'code': property_type_code,
            'name': property_name,
            'name_hebrew': property_name,
            'name_english': self._translate_property_type(property_name),
            'category': self._categorize_property_type(property_type_code),
            'description': self._get_property_type_description(property_type_code)
        }
        
        return details
    
    def _translate_property_type(self, hebrew_name):
        """
        Translate Hebrew property type names to English.
        
        Args:
            hebrew_name: Hebrew property type name
            
        Returns:
            English translation
        """
        translations = {
            'דירה': 'Apartment',
            'דירה עם גינה': 'Apartment with Garden',
            'וילה': 'Villa',
            'נטהאוס': 'Penthouse',
            'בניין': 'Building',
            'קרקע': 'Land',
            'לופט': 'Loft',
            'טריפלקס': 'Triplex',
            'דירת גן': 'Garden Apartment',
            'גג': 'Rooftop',
            'יחידה': 'Unit',
            'מיני פנטהאוס': 'Mini Penthouse',
            'בית': 'House'
        }
        
        return translations.get(hebrew_name, hebrew_name)
    
    def _categorize_property_type(self, property_type_code):
        """
        Categorize property types into main categories.
        
        Args:
            property_type_code: Property type code
            
        Returns:
            Category name
        """
        residential = [1, 3, 5, 6, 31, 32, 34, 35, 36, 37, 39]
        commercial = [15]
        land = [33]
        
        code = int(property_type_code)
        if code in residential:
            return 'Residential'
        elif code in commercial:
            return 'Commercial'
        elif code in land:
            return 'Land'
        else:
            return 'Other'
    
    def _get_property_type_description(self, property_type_code):
        """
        Get detailed description for property type.
        
        Args:
            property_type_code: Property type code
            
        Returns:
            Description string
        """
        descriptions = {
            1: 'Standard apartment unit in a residential building',
            3: 'Apartment with private garden or outdoor space',
            5: 'Detached house with private land',
            6: 'Luxury apartment on the top floor of a building',
            15: 'Commercial building or structure',
            33: 'Vacant land for development',
            31: 'Open-concept living space, often in converted industrial buildings',
            32: 'Three-level apartment or house',
            34: 'Ground floor apartment with garden access',
            35: 'Apartment or unit on the roof of a building',
            36: 'Individual unit in a larger complex',
            37: 'Smaller version of a penthouse',
            39: 'Single-family house'
        }
        
        return descriptions.get(int(property_type_code), 'No description available')
    
    def get_comprehensive_property_info(self, property_type_code=None):
        """
        Get comprehensive information about property types and their characteristics.
        
        Args:
            property_type_code: Optional specific property type code
            
        Returns:
            Dict containing comprehensive property information
        """
        if property_type_code:
            # Return specific property type info
            return self.get_property_type_details(property_type_code)
        
        # Return comprehensive info for all property types
        all_types = self.get_all_property_type_codes()
        comprehensive_info = {}
        
        for code in all_types.keys():
            comprehensive_info[code] = self.get_property_type_details(code)
        
        return {
            'total_property_types': len(comprehensive_info),
            'property_types': comprehensive_info,
            'categories': {
                'residential': len([p for p in comprehensive_info.values() if p and p['category'] == 'Residential']),
                'commercial': len([p for p in comprehensive_info.values() if p and p['category'] == 'Commercial']),
                'land': len([p for p in comprehensive_info.values() if p and p['category'] == 'Land']),
                'other': len([p for p in comprehensive_info.values() if p and p['category'] == 'Other'])
            }
        }
    
    def search_properties_by_criteria(self, **criteria):
        """
        Search for properties based on multiple criteria.
        
        Args:
            **criteria: Search criteria (property_type, location, price_range, etc.)
            
        Returns:
            Dict containing search results and recommendations
        """
        search_results = {
            'criteria': criteria,
            'recommendations': [],
            'property_types': [],
            'locations': [],
            'price_ranges': []
        }
        
        # Property type recommendations
        if 'property_type' in criteria:
            property_type = criteria['property_type']
            if isinstance(property_type, str):
                # Search by name
                matching_codes = self.get_property_type_codes_by_name(property_type)
                search_results['property_types'] = matching_codes
            elif isinstance(property_type, int):
                # Direct code
                details = self.get_property_type_details(property_type)
                if details:
                    search_results['property_types'] = [property_type]
        
        # Location recommendations
        if 'location' in criteria:
            location = criteria['location']
            location_data = self.search_locations(location)
            search_results['locations'] = location_data
        
        # Price range recommendations
        if 'price_range' in criteria:
            price_range = criteria['price_range']
            if isinstance(price_range, dict):
                min_price = price_range.get('min')
                max_price = price_range.get('max')
                
                if min_price and max_price:
                    search_results['price_ranges'] = {
                        'min': min_price,
                        'max': max_price,
                        'range': f"{min_price:,} - {max_price:,} ₪"
                    }
        
        # Generate recommendations
        if search_results['property_types']:
            search_results['recommendations'].append({
                'type': 'property_type',
                'message': f"Found {len(search_results['property_types'])} matching property types",
                'data': search_results['property_types']
            })
        
        if search_results['locations']:
            search_results['recommendations'].append({
                'type': 'location',
                'message': f"Found location data for '{criteria.get('location', '')}'",
                'data': search_results['locations']
            })
        
        return search_results
    
    def get_property_type_statistics(self):
        """
        Get statistics about property types including counts and categories.
        
        Returns:
            Dict containing property type statistics
        """
        all_types = self.get_all_property_type_codes()
        comprehensive_info = self.get_comprehensive_property_info()
        
        # Count by category
        category_counts = comprehensive_info.get('categories', {})
        
        # Count by language
        hebrew_names = [name for name in all_types.values() if name and any('\u0590' <= char <= '\u05FF' for char in name)]
        english_names = [name for name in all_types.values() if name and not any('\u0590' <= char <= '\u05FF' for char in name)]
        
        statistics = {
            'total_property_types': len(all_types),
            'categories': category_counts,
            'language_distribution': {
                'hebrew': len(hebrew_names),
                'english': len(english_names)
            },
            'property_type_codes': {
                'min_code': min(all_types.keys()) if all_types else None,
                'max_code': max(all_types.keys()) if all_types else None,
                'code_range': f"{min(all_types.keys()) if all_types else 0} - {max(all_types.keys()) if all_types else 0}"
            },
            'most_common_categories': sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        }
        
        return statistics
    
    def validate_property_type_code(self, code):
        """
        Validate if a property type code exists and is valid.
        
        Args:
            code: Property type code to validate
            
        Returns:
            Dict containing validation result and details
        """
        try:
            code_int = int(code)
            all_types = self.get_all_property_type_codes()
            
            if code_int in all_types:
                details = self.get_property_type_details(code_int)
                return {
                    'valid': True,
                    'code': code_int,
                    'name': all_types[code_int],
                    'details': details,
                    'message': f"Valid property type: {all_types[code_int]}"
                }
            else:
                return {
                    'valid': False,
                    'code': code_int,
                    'message': f"Invalid property type code: {code_int}",
                    'available_codes': list(all_types.keys()),
                    'suggestion': f"Try one of: {', '.join(map(str, sorted(all_types.keys())))}"
                }
                
        except (ValueError, TypeError):
            return {
                'valid': False,
                'code': code,
                'message': f"Invalid code format: {code} (must be a number)",
                'available_codes': list(self.get_all_property_type_codes().keys())
            }
    
    def get_property_type_suggestions(self, partial_name):
        """
        Get property type suggestions based on partial name input.
        
        Args:
            partial_name: Partial property type name
            
        Returns:
            List of matching property type suggestions
        """
        if not partial_name or len(partial_name) < 2:
            return []
        
        all_types = self.get_all_property_type_codes()
        suggestions = []
        
        partial_lower = partial_name.lower()
        
        for code, name in all_types.items():
            if partial_lower in name.lower():
                suggestions.append({
                    'code': code,
                    'name': name,
                    'relevance_score': len(partial_lower) / len(name.lower()),
                    'details': self.get_property_type_details(code)
                })
        
        # Sort by relevance score (higher is better)
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def get_property_type_mapping(self, source_format='yad2', target_format='english'):
        """
        Get property type mapping between different formats.
        
        Args:
            source_format: Source format ('yad2', 'english', 'hebrew')
            target_format: Target format ('yad2', 'english', 'hebrew')
            
        Returns:
            Dict containing property type mappings
        """
        all_types = self.get_all_property_type_codes()
        mapping = {}
        
        for code, hebrew_name in all_types.items():
            english_name = self._translate_property_type(hebrew_name)
            
            if source_format == 'yad2' and target_format == 'english':
                mapping[code] = english_name
            elif source_format == 'yad2' and target_format == 'hebrew':
                mapping[code] = hebrew_name
            elif source_format == 'english' and target_format == 'yad2':
                mapping[english_name] = code
            elif source_format == 'hebrew' and target_format == 'yad2':
                mapping[hebrew_name] = code
            elif source_format == 'english' and target_format == 'hebrew':
                mapping[english_name] = hebrew_name
            elif source_format == 'hebrew' and target_format == 'english':
                mapping[hebrew_name] = english_name
        
        return mapping
    
    def convert_property_type(self, value, from_format, to_format):
        """
        Convert property type between different formats.
        
        Args:
            value: Property type value to convert
            from_format: Source format ('yad2', 'english', 'hebrew')
            to_format: Target format ('yad2', 'english', 'hebrew')
            
        Returns:
            Converted value or None if conversion not possible
        """
        if from_format == to_format:
            return value
        
        all_types = self.get_all_property_type_codes()
        
        # Convert to Yad2 code first if needed
        yad2_code = None
        if from_format == 'yad2':
            yad2_code = int(value)
        elif from_format == 'english':
            # Find by English name
            for code, hebrew_name in all_types.items():
                if self._translate_property_type(hebrew_name) == value:
                    yad2_code = code
                    break
        elif from_format == 'hebrew':
            # Find by Hebrew name
            for code, hebrew_name in all_types.items():
                if hebrew_name == value:
                    yad2_code = code
                    break
        
        if yad2_code is None:
            return None
        
        # Convert from Yad2 code to target format
        if to_format == 'yad2':
            return yad2_code
        elif to_format == 'english':
            hebrew_name = all_types.get(yad2_code)
            return self._translate_property_type(hebrew_name) if hebrew_name else None
        elif to_format == 'hebrew':
            return all_types.get(yad2_code)
        
        return None
    
    def get_property_type_aliases(self):
        """
        Get common aliases and alternative names for property types.
        
        Returns:
            Dict containing property type aliases
        """
        aliases = {
            'דירה': ['apartment', 'flat', 'unit', 'condo'],
            'דירה עם גינה': ['garden apartment', 'apartment with garden', 'ground floor apartment'],
            'וילה': ['villa', 'house', 'detached house', 'single family home'],
            'נטהאוס': ['penthouse', 'penthouse apartment', 'top floor luxury'],
            'בניין': ['building', 'commercial building', 'structure'],
            'קרקע': ['land', 'plot', 'vacant land', 'development land'],
            'לופט': ['loft', 'open space', 'industrial conversion', 'studio loft'],
            'טריפלקס': ['triplex', 'three level', 'three story', 'multi level'],
            'דירת גן': ['garden apartment', 'ground floor with garden', 'patio apartment'],
            'גג': ['rooftop', 'roof apartment', 'top floor', 'attic'],
            'יחידה': ['unit', 'apartment unit', 'residential unit'],
            'מיני פנטהאוס': ['mini penthouse', 'small penthouse', 'compact penthouse'],
            'בית': ['house', 'home', 'residence', 'dwelling']
        }
        
        return aliases
    
    def find_property_type_by_alias(self, alias):
        """
        Find property type by alias or alternative name.
        
        Args:
            alias: Alias or alternative name to search for
            
        Returns:
            List of matching property types with their codes
        """
        aliases = self.get_property_type_aliases()
        matches = []
        
        alias_lower = alias.lower()
        
        for hebrew_name, alias_list in aliases.items():
            if (alias_lower in hebrew_name.lower() or 
                any(alias_lower in alt.lower() for alt in alias_list)):
                
                # Find the code for this property type
                for code, name in self.get_all_property_type_codes().items():
                    if name == hebrew_name:
                        matches.append({
                            'code': code,
                            'name': hebrew_name,
                            'english_name': self._translate_property_type(hebrew_name),
                            'aliases': alias_list,
                            'match_type': 'exact' if alias_lower == hebrew_name.lower() else 'alias'
                        })
                        break
        
        return matches
    
    def compare_property_types(self, type1, type2):
        """
        Compare two property types and show their differences.
        
        Args:
            type1: First property type (code or name)
            type2: Second property type (code or name)
            
        Returns:
            Dict containing comparison results
        """
        # Get property type details
        details1 = None
        details2 = None
        
        if isinstance(type1, int):
            details1 = self.get_property_type_details(type1)
        else:
            # Try to find by name
            suggestions = self.get_property_type_suggestions(type1)
            if suggestions:
                details1 = suggestions[0]['details']
        
        if isinstance(type2, int):
            details2 = self.get_property_type_details(type2)
        else:
            # Try to find by name
            suggestions = self.get_property_type_suggestions(type2)
            if suggestions:
                details2 = suggestions[0]['details']
        
        if not details1 or not details2:
            return {
                'error': 'Could not find one or both property types',
                'type1_found': bool(details1),
                'type2_found': bool(details2)
            }
        
        # Compare properties
        comparison = {
            'type1': details1,
            'type2': details2,
            'similarities': [],
            'differences': [],
            'recommendation': ''
        }
        
        # Check similarities
        if details1['category'] == details2['category']:
            comparison['similarities'].append(f"Both are {details1['category']} properties")
        
        if details1['name'] == details2['name']:
            comparison['similarities'].append("Same property type")
        
        # Check differences
        if details1['category'] != details2['category']:
            comparison['differences'].append(f"Category: {details1['category']} vs {details2['category']}")
        
        if details1['description'] != details2['description']:
            comparison['differences'].append("Different characteristics")
        
        # Generate recommendation
        if details1['category'] == 'Residential' and details2['category'] == 'Commercial':
            comparison['recommendation'] = f"{details1['name']} is residential while {details2['name']} is commercial"
        elif details1['category'] == details2['category']:
            comparison['recommendation'] = f"Both {details1['name']} and {details2['name']} are {details1['category']} properties"
        
        return comparison
    
    def get_property_type_recommendations(self, criteria):
        """
        Get property type recommendations based on specific criteria.
        
        Args:
            criteria: Dict containing criteria like budget, location, family_size, etc.
            
        Returns:
            List of recommended property types with scores
        """
        recommendations = []
        all_types = self.get_all_property_type_codes()
        
        for code, name in all_types.items():
            details = self.get_property_type_details(code)
            if not details:
                continue
            
            score = 0
            reasons = []
            
            # Budget considerations
            if 'budget' in criteria:
                budget = criteria['budget']
                if budget < 1000000:  # Less than 1M NIS
                    if details['category'] == 'Land':
                        score += 3
                        reasons.append("Land is typically more affordable")
                    elif details['category'] == 'Residential':
                        score += 2
                        reasons.append("Residential properties in this budget range")
                elif budget > 5000000:  # More than 5M NIS
                    if details['name'] in ['וילה', 'נטהאוס']:
                        score += 3
                        reasons.append("Luxury properties suitable for high budget")
            
            # Family size considerations
            if 'family_size' in criteria:
                family_size = criteria['family_size']
                if family_size > 4:
                    if details['name'] in ['וילה', 'בית', 'טריפלקס']:
                        score += 3
                        reasons.append("Large properties suitable for big families")
                elif family_size <= 2:
                    if details['name'] in ['דירה', 'לופט', 'מיני פנטהאוס']:
                        score += 2
                        reasons.append("Compact properties suitable for small families")
            
            # Location considerations
            if 'location' in criteria:
                location = criteria['location']
                if 'תל אביב' in location or 'רמת גן' in location:
                    if details['name'] in ['דירה', 'נטהאוס']:
                        score += 2
                        reasons.append("Popular in urban areas")
                elif 'כפר' in location or 'מושב' in location:
                    if details['name'] in ['וילה', 'בית', 'קרקע']:
                        score += 2
                        reasons.append("Suitable for rural areas")
            
            # Investment considerations
            if criteria.get('investment', False):
                if details['name'] in ['דירה', 'בניין']:
                    score += 3
                    reasons.append("Good for rental income")
                elif details['name'] == 'קרקע':
                    score += 2
                    reasons.append("Potential for development")
            
            if score > 0:
                recommendations.append({
                    'code': code,
                    'name': name,
                    'score': score,
                    'reasons': reasons,
                    'details': details
                })
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def get_property_type_trends(self):
        """
        Get current trends and market insights for different property types.
        This is a placeholder for future integration with market data APIs.
        
        Returns:
            Dict containing property type trends and insights
        """
        # This would ideally fetch from market data APIs
        # For now, we'll provide static insights based on general market knowledge
        
        trends = {
            'residential': {
                'trend': 'stable',
                'demand': 'high',
                'price_movement': 'moderate_increase',
                'insights': [
                    'Apartments remain the most popular choice',
                    'Garden apartments are in high demand',
                    'Penthouse market shows luxury segment growth'
                ]
            },
            'commercial': {
                'trend': 'recovering',
                'demand': 'moderate',
                'price_movement': 'stable',
                'insights': [
                    'Office space demand varies by location',
                    'Retail properties adapting to e-commerce',
                    'Industrial properties showing steady growth'
                ]
            },
            'land': {
                'trend': 'growing',
                'demand': 'increasing',
                'price_movement': 'strong_increase',
                'insights': [
                    'Development land prices rising',
                    'Agricultural land conversion opportunities',
                    'Strategic locations commanding premium prices'
                ]
            }
        }
        
        return {
            'source': 'market_analysis',
            'last_updated': datetime.now().isoformat(),
            'trends': trends,
            'note': 'This is static data. For real-time trends, integrate with market data APIs.'
        }
    
    def get_property_type_market_analysis(self, property_type_code=None):
        """
        Get market analysis for specific property type or all types.
        
        Args:
            property_type_code: Optional specific property type code
            
        Returns:
            Dict containing market analysis data
        """
        if property_type_code:
            # Return analysis for specific property type
            details = self.get_property_type_details(property_type_code)
            if not details:
                return None
            
            # Generate specific analysis
            analysis = {
                'property_type': details,
                'market_position': self._analyze_market_position(details),
                'investment_potential': self._analyze_investment_potential(details),
                'risks': self._analyze_risks(details),
                'opportunities': self._analyze_opportunities(details)
            }
            
            return analysis
        
        # Return analysis for all property types
        all_types = self.get_all_property_type_codes()
        comprehensive_analysis = {}
        
        for code in all_types.keys():
            comprehensive_analysis[code] = self.get_property_type_market_analysis(code)
        
        return {
            'total_analyzed': len(comprehensive_analysis),
            'analysis': comprehensive_analysis,
            'summary': self._generate_market_summary(comprehensive_analysis)
        }
    
    def _analyze_market_position(self, property_details):
        """Analyze market position for a property type."""
        category = property_details.get('category', '')
        name = property_details.get('name', '')
        
        if category == 'Residential':
            if 'דירה' in name:
                return 'Core market segment - high liquidity'
            elif 'וילה' in name or 'נטהאוס' in name:
                return 'Premium segment - selective buyers'
            else:
                return 'Specialized segment - niche market'
        elif category == 'Commercial':
            return 'Business market - depends on economic conditions'
        elif category == 'Land':
            return 'Development market - long-term investment'
        else:
            return 'Specialized market - variable demand'
    
    def _analyze_investment_potential(self, property_details):
        """Analyze investment potential for a property type."""
        category = property_details.get('category', '')
        name = property_details.get('name', '')
        
        if category == 'Residential':
            if 'דירה' in name:
                return 'High - steady rental income, good appreciation'
            elif 'וילה' in name:
                return 'Medium-High - luxury market, selective tenants'
            else:
                return 'Medium - depends on location and market'
        elif category == 'Commercial':
            return 'Medium - business cycle dependent, higher yields'
        elif category == 'Land':
            return 'High - development potential, long-term appreciation'
        else:
            return 'Variable - depends on specific circumstances'
    
    def _analyze_risks(self, property_details):
        """Analyze risks for a property type."""
        category = property_details.get('category', '')
        name = property_details.get('name', '')
        
        risks = []
        
        if category == 'Residential':
            if 'דירה' in name:
                risks.extend(['Market saturation', 'Regulatory changes', 'Interest rate sensitivity'])
            elif 'וילה' in name:
                risks.extend(['High maintenance costs', 'Limited buyer pool', 'Economic sensitivity'])
        elif category == 'Commercial':
            risks.extend(['Business cycle risk', 'Tenant dependency', 'Regulatory changes'])
        elif category == 'Land':
            risks.extend(['Development approval risk', 'Market timing risk', 'Infrastructure dependency'])
        
        return risks
    
    def _analyze_opportunities(self, property_details):
        """Analyze opportunities for a property type."""
        category = property_details.get('category', '')
        name = property_details.get('name', '')
        
        opportunities = []
        
        if category == 'Residential':
            if 'דירה' in name:
                opportunities.extend(['Steady rental income', 'Population growth', 'Urban development'])
            elif 'וילה' in name:
                opportunities.extend(['Luxury market growth', 'Foreign investment', 'Lifestyle demand'])
        elif category == 'Commercial':
            opportunities.extend(['Business expansion', 'Technology adaptation', 'Market diversification'])
        elif category == 'Land':
            opportunities.extend(['Development potential', 'Infrastructure growth', 'Strategic location value'])
        
        return opportunities
    
    def _generate_market_summary(self, comprehensive_analysis):
        """Generate market summary from comprehensive analysis."""
        total_analyzed = len(comprehensive_analysis)
        residential_count = 0
        commercial_count = 0
        land_count = 0
        
        for analysis in comprehensive_analysis.values():
            if analysis and 'property_type' in analysis:
                category = analysis['property_type'].get('category', '')
                if category == 'Residential':
                    residential_count += 1
                elif category == 'Commercial':
                    commercial_count += 1
                elif category == 'Land':
                    land_count += 1
        
        return {
            'total_property_types': total_analyzed,
            'category_distribution': {
                'residential': residential_count,
                'commercial': commercial_count,
                'land': land_count
            },
            'market_overview': 'Comprehensive analysis of all property types in the market',
            'recommendation': 'Diversify across categories based on investment goals and risk tolerance'
        }
    
    def export_property_types_to_csv(self, filename=None):
        """
        Export property types data to CSV format.
        
        Args:
            filename: Optional filename, defaults to timestamped filename
            
        Returns:
            Filename where data was saved
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yad2_property_types_{timestamp}.csv"
        
        import csv
        
        all_types = self.get_all_property_type_codes()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['code', 'name_hebrew', 'name_english', 'category', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for code, hebrew_name in all_types.items():
                details = self.get_property_type_details(code)
                if details:
                    writer.writerow({
                        'code': code,
                        'name_hebrew': details.get('name_hebrew', hebrew_name),
                        'name_english': details.get('name_english', ''),
                        'category': details.get('category', ''),
                        'description': details.get('description', '')
                    })
        
        print(f"Exported {len(all_types)} property types to {filename}")
        return filename
    
    def export_property_types_to_excel(self, filename=None):
        """
        Export property types data to Excel format.
        
        Args:
            filename: Optional filename, defaults to timestamped filename
            
        Returns:
            Filename where data was saved
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yad2_property_types_{timestamp}.xlsx"
        
        try:
            import pandas as pd
            
            all_types = self.get_all_property_type_codes()
            data = []
            
            for code, hebrew_name in all_types.items():
                details = self.get_property_type_details(code)
                if details:
                    data.append({
                        'Code': code,
                        'Name (Hebrew)': details.get('name_hebrew', hebrew_name),
                        'Name (English)': details.get('name_english', ''),
                        'Category': details.get('category', ''),
                        'Description': details.get('description', ''),
                        'Aliases': ', '.join(self.get_property_type_aliases().get(hebrew_name, []))
                    })
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, sheet_name='Property Types')
            
            print(f"Exported {len(data)} property types to {filename}")
            return filename
            
        except ImportError:
            print("pandas is required for Excel export. Install with: pip install pandas openpyxl")
            return None
    
    def get_property_type_search_history(self):
        """
        Get search history for property types (placeholder for future implementation).
        
        Returns:
            Dict containing search history information
        """
        # This would ideally store and retrieve actual search history
        # For now, we'll return a placeholder structure
        
        return {
            'feature': 'search_history',
            'status': 'not_implemented',
            'message': 'Search history tracking not yet implemented',
            'suggested_implementation': [
                'Store search queries in database',
                'Track user preferences',
                'Provide personalized recommendations',
                'Analyze search patterns'
            ]
        }
    
    def get_property_type_popularity(self):
        """
        Get popularity metrics for different property types (placeholder for future implementation).
        
        Returns:
            Dict containing popularity data
        """
        # This would ideally fetch from analytics APIs or databases
        # For now, we'll provide estimated popularity based on market knowledge
        
        all_types = self.get_all_property_type_codes()
        popularity_data = {}
        
        for code, name in all_types.items():
            details = self.get_property_type_details(code)
            if details:
                # Assign estimated popularity scores
                if details['category'] == 'Residential':
                    if 'דירה' in name:
                        popularity_score = 95  # Most popular
                    elif 'וילה' in name:
                        popularity_score = 70  # Popular but niche
                    else:
                        popularity_score = 60  # Moderate popularity
                elif details['category'] == 'Commercial':
                    popularity_score = 40  # Business market
                elif details['category'] == 'Land':
                    popularity_score = 30  # Development market
                else:
                    popularity_score = 50  # Default
                
                popularity_data[code] = {
                    'name': name,
                    'popularity_score': popularity_score,
                    'popularity_level': self._get_popularity_level(popularity_score),
                    'category': details['category']
                }
        
        return {
            'source': 'estimated_popularity',
            'last_updated': datetime.now().isoformat(),
            'popularity_data': popularity_data,
            'note': 'This is estimated data. For real popularity metrics, integrate with analytics APIs.'
        }
    
    def _get_popularity_level(self, score):
        """Convert popularity score to descriptive level."""
        if score >= 90:
            return 'Very High'
        elif score >= 80:
            return 'High'
        elif score >= 70:
            return 'Medium-High'
        elif score >= 60:
            return 'Medium'
        elif score >= 50:
            return 'Medium-Low'
        elif score >= 40:
            return 'Low'
        else:
            return 'Very Low'
    
    def get_property_type_comparison_table(self):
        """
        Generate a comparison table for all property types.
        
        Returns:
            Dict containing comparison table data
        """
        all_types = self.get_all_property_type_codes()
        comparison_data = []
        
        for code, name in all_types.items():
            details = self.get_property_type_details(code)
            if details:
                comparison_data.append({
                    'code': code,
                    'name_hebrew': details.get('name_hebrew', name),
                    'name_english': details.get('name_english', ''),
                    'category': details.get('category', ''),
                    'description': details.get('description', ''),
                    'aliases': ', '.join(self.get_property_type_aliases().get(name, [])),
                    'investment_potential': self._analyze_investment_potential(details),
                    'market_position': self._analyze_market_position(details)
                })
        
        return {
            'total_property_types': len(comparison_data),
            'comparison_table': comparison_data,
            'generated_at': datetime.now().isoformat(),
            'columns': [
                'Code', 'Name (Hebrew)', 'Name (English)', 'Category', 
                'Description', 'Aliases', 'Investment Potential', 'Market Position'
            ]
        }
    
    def get_property_type_api_endpoints(self):
        """
        Get information about available API endpoints for property types.
        
        Returns:
            Dict containing API endpoint information
        """
        endpoints = {
            'yad2_api': {
                'base_url': self.api_base_url,
                'endpoints': [
                    {
                        'path': '/address-autocomplete/realestate/v2',
                        'method': 'GET',
                        'description': 'Address autocomplete for real estate',
                        'parameters': ['text'],
                        'example': f"{self.api_base_url}/address-autocomplete/realestate/v2?text=רמת"
                    },
                    {
                        'path': '/property-types',
                        'method': 'GET',
                        'description': 'Property types list (placeholder)',
                        'parameters': [],
                        'example': f"{self.api_base_url}/property-types",
                        'status': 'to_be_discovered'
                    }
                ]
            },
            'external_apis': {
                'madlan': {
                    'url': 'https://www.madlan.co.il/api',
                    'description': 'Madlan real estate API',
                    'status': 'not_integrated'
                },
                'homeless': {
                    'url': 'https://www.homeless.co.il/api',
                    'description': 'Homeless real estate API',
                    'status': 'not_integrated'
                }
            }
        }
        
        return endpoints
    
    def get_property_type_documentation(self):
        """
        Get comprehensive documentation for property types and their usage.
        
        Returns:
            Dict containing documentation information
        """
        documentation = {
            'overview': {
                'title': 'Yad2 Property Types Documentation',
                'description': 'Comprehensive guide to property types in the Israeli real estate market',
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat()
            },
            'property_types': {},
            'usage_examples': [
                {
                    'title': 'Get all property types',
                    'code': 'scraper = Yad2Scraper()\nall_types = scraper.get_all_property_type_codes()',
                    'description': 'Retrieve all available property type codes and names'
                },
                {
                    'title': 'Search property types by name',
                    'code': 'results = scraper.search_property_types("דירה")',
                    'description': 'Search for property types containing specific text'
                },
                {
                    'title': 'Get property type details',
                    'code': 'details = scraper.get_property_type_details(1)',
                    'description': 'Get detailed information about a specific property type'
                },
                {
                    'title': 'Convert between formats',
                    'code': 'english_name = scraper.convert_property_type(1, "yad2", "english")',
                    'description': 'Convert property type from Yad2 code to English name'
                },
                {
                    'title': 'Export to different formats',
                    'code': 'scraper.export_codes_to_json("property_types.json")\nscraper.export_property_types_to_csv("property_types.csv")',
                    'description': 'Export property type data to various file formats'
                }
            ],
            'api_reference': {
                'methods': [
                    'get_all_property_type_codes()',
                    'search_property_types(search_term)',
                    'get_property_type_details(code)',
                    'get_property_type_by_code(code)',
                    'get_property_type_codes_by_name(name)',
                    'convert_property_type(value, from_format, to_format)',
                    'get_property_type_aliases()',
                    'find_property_type_by_alias(alias)',
                    'compare_property_types(type1, type2)',
                    'get_property_type_recommendations(criteria)',
                    'get_property_type_trends()',
                    'get_property_type_market_analysis(code)',
                    'export_codes_to_json(filename)',
                    'export_property_types_to_csv(filename)',
                    'export_property_types_to_excel(filename)',
                    'print_codes_summary()'
                ]
            },
            'data_formats': {
                'yad2': 'Numeric codes used by Yad2 (e.g., 1, 3, 5)',
                'hebrew': 'Hebrew names (e.g., "דירה", "וילה")',
                'english': 'English translations (e.g., "Apartment", "Villa")'
            },
            'categories': {
                'residential': 'Properties designed for living (apartments, houses, villas)',
                'commercial': 'Properties designed for business use (offices, retail, industrial)',
                'land': 'Vacant land for development or investment'
            }
        }
        
        # Add documentation for each property type
        all_types = self.get_all_property_type_codes()
        for code, name in all_types.items():
            details = self.get_property_type_details(code)
            if details:
                documentation['property_types'][code] = {
                    'name': name,
                    'english_name': details.get('name_english', ''),
                    'category': details.get('category', ''),
                    'description': details.get('description', ''),
                    'aliases': self.get_property_type_aliases().get(name, []),
                    'usage_tips': self._get_usage_tips(details)
                }
        
        return documentation
    
    def _get_usage_tips(self, property_details):
        """Generate usage tips for a property type."""
        category = property_details.get('category', '')
        name = property_details.get('name', '')
        
        tips = []
        
        if category == 'Residential':
            if 'דירה' in name:
                tips.extend([
                    'Most common property type for families',
                    'Good for first-time buyers',
                    'Suitable for rental investment',
                    'Check building maintenance and neighbors'
                ])
            elif 'וילה' in name:
                tips.extend([
                    'Premium property with privacy',
                    'Higher maintenance costs',
                    'Good for large families',
                    'Check neighborhood security'
                ])
        elif category == 'Commercial':
            tips.extend([
                'Verify zoning regulations',
                'Check parking availability',
                'Consider business hours restrictions',
                'Evaluate foot traffic and accessibility'
            ])
        elif category == 'Land':
            tips.extend([
                'Verify development permits',
                'Check infrastructure availability',
                'Consider long-term investment horizon',
                'Research zoning changes'
            ])
        
        return tips
    
    def get_property_type_cheat_sheet(self):
        """
        Get a quick reference cheat sheet for property types.
        
        Returns:
            Dict containing cheat sheet information
        """
        all_types = self.get_all_property_type_codes()
        cheat_sheet = {
            'title': 'Yad2 Property Types Cheat Sheet',
            'quick_reference': {},
            'common_codes': {},
            'category_summary': {}
        }
        
        # Quick reference by code
        for code, name in all_types.items():
            details = self.get_property_type_details(code)
            if details:
                cheat_sheet['quick_reference'][code] = {
                    'name': name,
                    'english': details.get('name_english', ''),
                    'category': details.get('category', '')
                }
        
        # Common codes for quick access
        common_codes = {
            'דירה': 1,
            'וילה': 5,
            'נטהאוס': 6,
            'קרקע': 33,
            'בניין': 15
        }
        
        for hebrew_name, code in common_codes.items():
            if code in all_types:
                cheat_sheet['common_codes'][hebrew_name] = {
                    'code': code,
                    'english': self._translate_property_type(hebrew_name)
                }
        
        # Category summary
        categories = {}
        for code, name in all_types.items():
            details = self.get_property_type_details(code)
            if details:
                category = details.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'code': code,
                    'name': name
                })
        
        cheat_sheet['category_summary'] = categories
        
        return cheat_sheet
    
    def get_property_type_help(self):
        """
        Get comprehensive help and troubleshooting information for property types.
        
        Returns:
            Dict containing help information
        """
        help_info = {
            'title': 'Yad2 Property Types Help & Troubleshooting',
            'common_issues': [
                {
                    'issue': 'Property type code not found',
                    'solution': 'Use get_all_property_type_codes() to see all available codes',
                    'example': 'scraper.get_all_property_type_codes()'
                },
                {
                    'issue': 'Hebrew text not displaying correctly',
                    'solution': 'Ensure proper UTF-8 encoding and Hebrew font support',
                    'example': 'Use encoding="utf-8" when opening files'
                },
                {
                    'issue': 'Property type conversion failing',
                    'solution': 'Verify the source format and target format are correct',
                    'example': 'scraper.convert_property_type(1, "yad2", "english")'
                },
                {
                    'issue': 'Export not working',
                    'solution': 'Check file permissions and ensure required libraries are installed',
                    'example': 'pip install pandas openpyxl for Excel export'
                }
            ],
            'best_practices': [
                'Always validate property type codes before using them',
                'Use the built-in conversion methods for format changes',
                'Export data in UTF-8 encoding for Hebrew support',
                'Check the comprehensive documentation for detailed usage',
                'Use the cheat sheet for quick reference'
            ],
            'performance_tips': [
                'Cache property type data if making multiple calls',
                'Use specific methods instead of comprehensive ones when possible',
                'Export data once and reuse rather than regenerating',
                'Use search methods with specific terms for better performance'
            ],
            'error_handling': {
                'invalid_code': 'Use validate_property_type_code() to check codes',
                'missing_data': 'Check if property type exists before accessing details',
                'api_failures': 'Implement retry logic for external API calls',
                'export_errors': 'Verify file paths and permissions'
            }
        }
        
        return help_info
    
    def get_property_type_examples(self):
        """
        Get practical examples of how to use property type functionality.
        
        Returns:
            Dict containing example code and use cases
        """
        examples = {
            'title': 'Yad2 Property Types - Practical Examples',
            'basic_usage': [
                {
                    'title': 'Initialize scraper and get all property types',
                    'code': '''# Initialize the scraper
scraper = Yad2Scraper()

# Get all property type codes
all_types = scraper.get_all_property_type_codes()
print(f"Found {len(all_types)} property types")

# Print them in a nice format
scraper.print_codes_summary()''',
                    'description': 'Basic setup and retrieval of all property types'
                },
                {
                    'title': 'Search for specific property types',
                    'code': '''# Search by Hebrew name
apartments = scraper.search_property_types("דירה")
print(f"Found {len(apartments)} apartment types")

# Search by English name
villas = scraper.search_property_types("villa")
print(f"Found {len(villas)} villa types")''',
                    'description': 'Searching property types by name in different languages'
                },
                {
                    'title': 'Get detailed information about a property type',
                    'code': '''# Get details by code
details = scraper.get_property_type_details(1)
print(f"Property type: {details['name']}")
print(f"Category: {details['category']}")
print(f"Description: {details['description']}")

# Get details by name
villa_details = scraper.get_property_type_details(5)
print(f"Villa details: {villa_details}")''',
                    'description': 'Retrieving detailed information about specific property types'
                }
            ],
            'advanced_usage': [
                {
                    'title': 'Convert between different property type formats',
                    'code': '''# Convert Yad2 code to English name
english_name = scraper.convert_property_type(1, "yad2", "english")
print(f"Code 1 = {english_name}")

# Convert Hebrew name to Yad2 code
code = scraper.convert_property_type("וילה", "hebrew", "yad2")
print(f"וילה = Code {code}")

# Get mapping between formats
mapping = scraper.get_property_type_mapping("yad2", "english")
print(f"Mapping: {mapping}")''',
                    'description': 'Converting property types between different formats and getting mappings'
                },
                {
                    'title': 'Compare different property types',
                    'code': '''# Compare apartment vs villa
comparison = scraper.compare_property_types(1, 5)
print("Similarities:", comparison['similarities'])
print("Differences:", comparison['differences'])
print("Recommendation:", comparison['recommendation'])

# Compare by name
comparison2 = scraper.compare_property_types("דירה", "נטהאוס")
print(f"Comparison result: {comparison2}")''',
                    'description': 'Comparing different property types to understand differences'
                },
                {
                    'title': 'Get property type recommendations',
                    'code': '''# Get recommendations based on criteria
criteria = {
    'budget': 3000000,
    'family_size': 4,
    'location': 'תל אביב',
    'investment': True
}

recommendations = scraper.get_property_type_recommendations(**criteria)
for rec in recommendations:
    print(f"{rec['name']}: Score {rec['score']}")
    print(f"Reasons: {', '.join(rec['reasons'])}")''',
                    'description': 'Getting intelligent recommendations based on specific criteria'
                }
            ],
            'data_export': [
                {
                    'title': 'Export property types to different formats',
                    'code': '''# Export to JSON
json_file = scraper.export_codes_to_json("all_codes.json")

# Export to CSV
csv_file = scraper.export_property_types_to_csv("property_types.csv")

# Export to Excel (requires pandas)
excel_file = scraper.export_property_types_to_excel("property_types.xlsx")

print(f"Exported to: {json_file}, {csv_file}, {excel_file}")''',
                    'description': 'Exporting property type data to various file formats'
                },
                {
                    'title': 'Generate comparison tables and reports',
                    'code': '''# Get comparison table
comparison_table = scraper.get_property_type_comparison_table()
print(f"Generated comparison table with {comparison_table['total_property_types']} types")

# Get market analysis
market_analysis = scraper.get_property_type_market_analysis()
print(f"Market analysis for {market_analysis['total_analyzed']} property types")

# Get trends
trends = scraper.get_property_type_trends()
print(f"Current market trends: {trends['trends']}")''',
                    'description': 'Generating comprehensive reports and analysis'
                }
            ],
            'integration_examples': [
                {
                    'title': 'Integrate with search parameters',
                    'code': '''# Set search parameters with property type
scraper.set_search_parameters(
    property="1,5",  # Apartments and villas
    maxPrice=5000000,
    area=1  # Tel Aviv area
)

# Build search URL
search_url = scraper.build_search_url()
print(f"Search URL: {search_url}")

# Scrape listings
listings = scraper.scrape_all_pages(max_pages=3)
print(f"Found {len(listings)} listings")''',
                    'description': 'Integrating property types with the main scraping functionality'
                },
                {
                    'title': 'Use with location data',
                    'code': '''# Search for locations
location_data = scraper.search_locations("רמת")
print(f"Found {len(location_data['cities'])} cities")

# Get city information
city_info = scraper.get_city_by_id(8600)
print(f"City: {city_info['name']}")

# Combine with property type search
scraper.set_search_parameters(
    property=1,
    city=8600  # Ramat Gan
)''',
                    'description': 'Combining property types with location-based searches'
                }
            ]
        }
        
        return examples
    
    def get_property_type_summary(self):
        """
        Get a comprehensive summary of all property type functionality.
        
        Returns:
            Dict containing summary information
        """
        summary = {
            'title': 'Yad2 Property Types - Complete Functionality Summary',
            'total_methods': 0,
            'categories': {},
            'quick_start': {},
            'advanced_features': {},
            'export_options': {},
            'integration_points': {}
        }
        
        # Count total methods
        method_count = 0
        
        # Basic functionality
        basic_methods = [
            'get_all_property_type_codes()',
            'search_property_types()',
            'get_property_type_details()',
            'get_property_type_by_code()',
            'get_property_type_codes_by_name()'
        ]
        method_count += len(basic_methods)
        
        summary['categories']['basic'] = {
            'description': 'Core property type retrieval and search',
            'methods': basic_methods,
            'count': len(basic_methods)
        }
        
        # Conversion functionality
        conversion_methods = [
            'convert_property_type()',
            'get_property_type_mapping()',
            'get_property_type_aliases()',
            'find_property_type_by_alias()'
        ]
        method_count += len(conversion_methods)
        
        summary['categories']['conversion'] = {
            'description': 'Property type format conversion and mapping',
            'methods': conversion_methods,
            'count': len(conversion_methods)
        }
        
        # Analysis functionality
        analysis_methods = [
            'compare_property_types()',
            'get_property_type_recommendations()',
            'get_property_type_trends()',
            'get_property_type_market_analysis()',
            'get_property_type_statistics()'
        ]
        method_count += len(analysis_methods)
        
        summary['categories']['analysis'] = {
            'description': 'Property type analysis and market insights',
            'methods': analysis_methods,
            'count': len(analysis_methods)
        }
        
        # Export functionality
        export_methods = [
            'export_codes_to_json()',
            'export_property_types_to_csv()',
            'export_property_types_to_excel()',
            'get_property_type_comparison_table()'
        ]
        method_count += len(export_methods)
        
        summary['categories']['export'] = {
            'description': 'Data export and reporting capabilities',
            'methods': export_methods,
            'count': len(export_methods)
        }
        
        # Documentation functionality
        doc_methods = [
            'print_codes_summary()',
            'get_property_type_documentation()',
            'get_property_type_cheat_sheet()',
            'get_property_type_help()',
            'get_property_type_examples()'
        ]
        method_count += len(doc_methods)
        
        summary['categories']['documentation'] = {
            'description': 'Documentation and help resources',
            'methods': doc_methods,
            'count': len(doc_methods)
        }
        
        summary['total_methods'] = method_count
        
        # Quick start guide
        summary['quick_start'] = {
            'step1': 'Initialize: scraper = Yad2Scraper()',
            'step2': 'Get all types: all_types = scraper.get_all_property_type_codes()',
            'step3': 'Print summary: scraper.print_codes_summary()',
            'step4': 'Search types: results = scraper.search_property_types("דירה")',
            'step5': 'Get details: details = scraper.get_property_type_details(1)'
        }
        
        # Advanced features
        summary['advanced_features'] = {
            'market_analysis': 'Comprehensive market analysis for all property types',
            'recommendations': 'AI-powered property type recommendations',
            'trends': 'Market trends and insights',
            'comparisons': 'Detailed property type comparisons',
            'export_formats': 'Multiple export formats (JSON, CSV, Excel)'
        }
        
        # Export options
        summary['export_options'] = {
            'json': 'Structured data export with metadata',
            'csv': 'Spreadsheet-compatible format',
            'excel': 'Professional Excel format with formatting',
            'comparison_tables': 'Detailed comparison reports'
        }
        
        # Integration points
        summary['integration_points'] = {
            'search_parameters': 'Integrate with Yad2 search functionality',
            'location_data': 'Combine with address autocomplete API',
            'market_data': 'Future integration with market data APIs',
            'external_apis': 'Extensible architecture for external data sources'
        }
        
        return summary
    
    def get_property_type_quick_start(self):
        """
        Get a quick start guide for using property type functionality.
        
        Returns:
            Dict containing quick start information
        """
        quick_start = {
            'title': 'Yad2 Property Types - Quick Start Guide',
            'installation': {
                'step1': 'Ensure you have the required dependencies',
                'step2': 'Import the Yad2Scraper class',
                'step3': 'Initialize the scraper instance'
            },
            'basic_usage': {
                'step1': 'Get all available property types',
                'step2': 'Search for specific property types',
                'step3': 'Get detailed information',
                'step4': 'Convert between formats',
                'step5': 'Export data'
            },
            'code_examples': {
                'basic_setup': '''from yad2.scrapers.yad2_scraper import Yad2Scraper

# Initialize scraper
scraper = Yad2Scraper()

# Get all property types
all_types = scraper.get_all_property_types()
print(f"Found {len(all_types)} property types")''',
                
                'search_and_details': '''# Search for apartments
apartments = scraper.search_property_types("דירה")
print(f"Found {len(apartments)} apartment types")

# Get details for code 1
details = scraper.get_property_type_details(1)
print(f"Property: {details['name']}")
print(f"Category: {details['category']}")''',
                
                'conversion': '''# Convert Yad2 code to English
english_name = scraper.convert_property_type(1, "yad2", "english")
print(f"Code 1 = {english_name}")

# Convert Hebrew name to code
code = scraper.convert_property_type("וילה", "hebrew", "yad2")
print(f"וילה = Code {code}")''',
                
                'export': '''# Export to different formats
scraper.export_codes_to_json("property_types.json")
scraper.export_property_types_to_csv("property_types.csv")
scraper.export_property_types_to_excel("property_types.xlsx")''',
                
                'analysis': '''# Get market analysis
analysis = scraper.get_property_type_market_analysis()
print(f"Analyzed {analysis['total_analyzed']} property types")

# Get recommendations
recommendations = scraper.get_property_type_recommendations(
    budget=3000000, 
    family_size=4
)
for rec in recommendations[:3]:
    print(f"{rec['name']}: Score {rec['score']}")'''
            },
            'common_patterns': {
                'validation': 'Always validate property type codes before use',
                'caching': 'Cache results for better performance',
                'error_handling': 'Implement proper error handling for API calls',
                'format_consistency': 'Use consistent format throughout your application'
            },
            'next_steps': {
                'explore_advanced': 'Try market analysis and recommendations',
                'integrate_search': 'Combine with Yad2 search functionality',
                'custom_export': 'Create custom export formats for your needs',
                'extend_functionality': 'Add new property type categories or features'
            }
        }
        
        return quick_start
    
    def get_property_type_api_documentation(self):
        """
        Get comprehensive API documentation for property type functionality.
        
        Returns:
            Dict containing API documentation
        """
        api_docs = {
            'title': 'Yad2 Property Types - API Documentation',
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'overview': 'Complete API reference for property type functionality',
            'endpoints': {},
            'data_structures': {},
            'error_codes': {},
            'rate_limits': {},
            'authentication': {}
        }
        
        # API Endpoints
        api_docs['endpoints'] = {
            'property_types': {
                'get_all': {
                    'method': 'get_all_property_type_codes()',
                    'description': 'Retrieve all available property type codes and names',
                    'parameters': 'None',
                    'returns': 'Dict[int, str] - Mapping of codes to Hebrew names',
                    'example': 'all_types = scraper.get_all_property_type_codes()'
                },
                'search': {
                    'method': 'search_property_types(search_term)',
                    'description': 'Search property types by name or partial name',
                    'parameters': 'search_term (str) - Text to search for',
                    'returns': 'Dict[int, str] - Matching property types',
                    'example': 'results = scraper.search_property_types("דירה")'
                },
                'details': {
                    'method': 'get_property_type_details(code)',
                    'description': 'Get comprehensive details about a property type',
                    'parameters': 'code (int) - Property type code',
                    'returns': 'Dict - Property type details including category and description',
                    'example': 'details = scraper.get_property_type_details(1)'
                }
            },
            'conversion': {
                'convert': {
                    'method': 'convert_property_type(value, from_format, to_format)',
                    'description': 'Convert property type between different formats',
                    'parameters': 'value, from_format (str), to_format (str)',
                    'returns': 'Converted value or None if conversion not possible',
                    'example': 'english = scraper.convert_property_type(1, "yad2", "english")'
                },
                'mapping': {
                    'method': 'get_property_type_mapping(source_format, target_format)',
                    'description': 'Get mapping between different property type formats',
                    'parameters': 'source_format (str), target_format (str)',
                    'returns': 'Dict - Mapping between formats',
                    'example': 'mapping = scraper.get_property_type_mapping("yad2", "english")'
                }
            },
            'analysis': {
                'compare': {
                    'method': 'compare_property_types(type1, type2)',
                    'description': 'Compare two property types and show differences',
                    'parameters': 'type1, type2 - Property type codes or names',
                    'returns': 'Dict - Comparison results with similarities and differences',
                    'example': 'comparison = scraper.compare_property_types(1, 5)'
                },
                'recommendations': {
                    'method': 'get_property_type_recommendations(**criteria)',
                    'description': 'Get property type recommendations based on criteria',
                    'parameters': '**criteria - Search criteria (budget, location, etc.)',
                    'returns': 'List - Recommended property types with scores',
                    'example': 'recs = scraper.get_property_type_recommendations(budget=3000000)'
                },
                'market_analysis': {
                    'method': 'get_property_type_market_analysis(code=None)',
                    'description': 'Get market analysis for property types',
                    'parameters': 'code (int, optional) - Specific property type code',
                    'returns': 'Dict - Market analysis data',
                    'example': 'analysis = scraper.get_property_type_market_analysis()'
                }
            },
            'export': {
                'json': {
                    'method': 'export_codes_to_json(filename=None)',
                    'description': 'Export all codes to JSON format',
                    'parameters': 'filename (str, optional) - Output filename',
                    'returns': 'str - Filename where data was saved',
                    'example': 'file = scraper.export_codes_to_json("codes.json")'
                },
                'csv': {
                    'method': 'export_property_types_to_csv(filename=None)',
                    'description': 'Export property types to CSV format',
                    'parameters': 'filename (str, optional) - Output filename',
                    'returns': 'str - Filename where data was saved',
                    'example': 'file = scraper.export_property_types_to_csv("types.csv")'
                },
                'excel': {
                    'method': 'export_property_types_to_excel(filename=None)',
                    'description': 'Export property types to Excel format',
                    'parameters': 'filename (str, optional) - Output filename',
                    'returns': 'str - Filename where data was saved',
                    'example': 'file = scraper.export_property_types_to_excel("types.xlsx")'
                }
            }
        }
        
        # Data Structures
        api_docs['data_structures'] = {
            'property_type_details': {
                'code': 'int - Property type code',
                'name': 'str - Hebrew name',
                'name_hebrew': 'str - Hebrew name (same as name)',
                'name_english': 'str - English translation',
                'category': 'str - Category (Residential, Commercial, Land)',
                'description': 'str - Detailed description'
            },
            'comparison_result': {
                'type1': 'Dict - First property type details',
                'type2': 'Dict - Second property type details',
                'similarities': 'List[str] - List of similarities',
                'differences': 'List[str] - List of differences',
                'recommendation': 'str - Generated recommendation'
            },
            'recommendation': {
                'code': 'int - Property type code',
                'name': 'str - Property type name',
                'score': 'int - Recommendation score',
                'reasons': 'List[str] - List of reasons for recommendation',
                'details': 'Dict - Property type details'
            }
        }
        
        # Error Codes
        api_docs['error_codes'] = {
            'invalid_code': 'Property type code not found',
            'conversion_failed': 'Property type conversion not possible',
            'export_failed': 'Data export operation failed',
            'api_error': 'External API call failed',
            'validation_error': 'Input validation failed'
        }
        
        # Rate Limits
        api_docs['rate_limits'] = {
            'api_calls': 'No specific rate limits implemented',
            'recommendation': 'Implement reasonable delays between requests',
            'external_apis': 'Subject to external API rate limits'
        }
        
        # Authentication
        api_docs['authentication'] = {
            'required': 'No authentication required for basic functionality',
            'external_apis': 'May require API keys for external data sources',
            'headers': 'Uses standard HTTP headers for requests'
        }
        
        return api_docs
    
    def get_property_type_testing_examples(self):
        """
        Get testing examples and test cases for property type functionality.
        
        Returns:
            Dict containing testing examples
        """
        testing_examples = {
            'title': 'Yad2 Property Types - Testing Examples',
            'unit_tests': {},
            'integration_tests': {},
            'test_data': {},
            'assertion_examples': {},
            'mock_examples': {}
        }
        
        # Unit Tests
        testing_examples['unit_tests'] = {
            'test_get_all_property_types': '''def test_get_all_property_types():
    scraper = Yad2Scraper()
    all_types = scraper.get_all_property_type_codes()
    
    # Assertions
    assert isinstance(all_types, dict)
    assert len(all_types) > 0
    assert all(isinstance(k, int) for k in all_types.keys())
    assert all(isinstance(v, str) for v in all_types.values())
    
    # Check specific property types
    assert 1 in all_types  # דירה
    assert 5 in all_types  # וילה
    assert 33 in all_types  # קרקע''',
            
            'test_search_property_types': '''def test_search_property_types():
    scraper = Yad2Scraper()
    
    # Test Hebrew search
    hebrew_results = scraper.search_property_types("דירה")
    assert isinstance(hebrew_results, dict)
    assert len(hebrew_results) > 0
    
    # Test English search
    english_results = scraper.search_property_types("apartment")
    assert isinstance(english_results, dict)
    
    # Test empty search
    empty_results = scraper.search_property_types("")
    assert isinstance(empty_results, dict)''',
            
            'test_property_type_conversion': '''def test_property_type_conversion():
    scraper = Yad2Scraper()
    
    # Test Yad2 to English
    english = scraper.convert_property_type(1, "yad2", "english")
    assert english == "Apartment"
    
    # Test Hebrew to Yad2
    code = scraper.convert_property_type("וילה", "hebrew", "yad2")
    assert code == 5
    
    # Test invalid conversion
    result = scraper.convert_property_type(999, "yad2", "english")
    assert result is None''',
            
            'test_property_type_details': '''def test_property_type_details():
    scraper = Yad2Scraper()
    
    # Test valid code
    details = scraper.get_property_type_details(1)
    assert isinstance(details, dict)
    assert details['code'] == 1
    assert details['name'] == 'דירה'
    assert details['category'] == 'Residential'
    
    # Test invalid code
    invalid_details = scraper.get_property_type_details(999)
    assert invalid_details is None''',
            
            'test_export_functions': '''def test_export_functions():
    scraper = Yad2Scraper()
    
    # Test JSON export
    json_file = scraper.export_codes_to_json("test_codes.json")
    assert json_file.endswith(".json")
    assert os.path.exists(json_file)
    
    # Test CSV export
    csv_file = scraper.export_property_types_to_csv("test_types.csv")
    assert csv_file.endswith(".csv")
    assert os.path.exists(csv_file)
    
    # Cleanup
    os.remove(json_file)
    os.remove(csv_file)'''
        }
        
        # Integration Tests
        testing_examples['integration_tests'] = {
            'test_property_type_workflow': '''def test_property_type_workflow():
    scraper = Yad2Scraper()
    
    # Complete workflow test
    # 1. Get all types
    all_types = scraper.get_all_property_type_codes()
    assert len(all_types) > 0
    
    # 2. Search for specific type
    apartments = scraper.search_property_types("דירה")
    assert len(apartments) > 0
    
    # 3. Get details
    apartment_code = list(apartments.keys())[0]
    details = scraper.get_property_type_details(apartment_code)
    assert details is not None
    
    # 4. Convert to English
    english_name = scraper.convert_property_type(apartment_code, "yad2", "english")
    assert english_name is not None
    
    # 5. Export data
    export_file = scraper.export_codes_to_json("workflow_test.json")
    assert os.path.exists(export_file)
    
    # Cleanup
    os.remove(export_file)''',
            
            'test_market_analysis_integration': '''def test_market_analysis_integration():
    scraper = Yad2Scraper()
    
    # Test market analysis workflow
    analysis = scraper.get_property_type_market_analysis()
    assert analysis is not None
    assert 'total_analyzed' in analysis
    
    # Test specific property type analysis
    apartment_analysis = scraper.get_property_type_market_analysis(1)
    assert apartment_analysis is not None
    assert 'property_type' in apartment_analysis
    
    # Test recommendations
    recommendations = scraper.get_property_type_recommendations(budget=2000000)
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0'''
        }
        
        # Test Data
        testing_examples['test_data'] = {
            'valid_property_codes': [1, 3, 5, 6, 15, 33, 31, 32, 34, 35, 36, 37, 39],
            'invalid_property_codes': [999, -1, 0, 1000],
            'hebrew_names': ['דירה', 'וילה', 'נטהאוס', 'קרקע', 'בניין'],
            'english_names': ['Apartment', 'Villa', 'Penthouse', 'Land', 'Building'],
            'search_terms': ['דירה', 'villa', 'apartment', 'וילה', 'land']
        }
        
        # Assertion Examples
        testing_examples['assertion_examples'] = {
            'type_assertions': '''# Type assertions
assert isinstance(result, dict)
assert isinstance(result, list)
assert isinstance(result, str)
assert isinstance(result, int)''',
            
            'value_assertions': '''# Value assertions
assert len(result) > 0
assert result is not None
assert result != ""
assert result > 0''',
            
            'content_assertions': '''# Content assertions
assert "דירה" in result.values()
assert 1 in result.keys()
assert "Residential" in result['category']
assert result['code'] == 1''',
            
            'structure_assertions': '''# Structure assertions
assert 'code' in result
assert 'name' in result
assert 'category' in result
assert all(key in result for key in ['code', 'name', 'category'])'''
        }
        
        # Mock Examples
        testing_examples['mock_examples'] = {
            'mock_property_types': '''# Mock property types data
mock_property_types = {
    1: 'דירה',
    5: 'וילה',
    33: 'קרקע'
}

# Mock the method
@patch.object(Yad2Scraper, 'get_all_property_type_codes')
def test_with_mock(mock_method):
    mock_method.return_value = mock_property_types
    scraper = Yad2Scraper()
    result = scraper.get_all_property_type_codes()
    assert result == mock_property_types''',
            
            'mock_api_response': '''# Mock API response
mock_api_response = {
    'hoods': [{'fullTitleText': 'רמות, ירושלים', 'cityId': '3000'}],
    'cities': [{'fullTitleText': 'רמת גן', 'cityId': '8600'}]
}

@patch.object(requests.Session, 'get')
def test_api_call(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_api_response
    mock_get.return_value = mock_response
    
    scraper = Yad2Scraper()
    result = scraper.fetch_location_data("רמת")
    assert result['cities'][0]['fullTitleText'] == 'רמת גן' '''
        }
        
        return testing_examples
    
    def get_property_type_faq(self):
        """
        Get frequently asked questions about property type functionality.
        
        Returns:
            Dict containing FAQ information
        """
        faq = {
            'title': 'Yad2 Property Types - Frequently Asked Questions',
            'questions': [
                {
                    'question': 'What property types are available in Yad2?',
                    'answer': 'Yad2 supports various property types including apartments (דירה), villas (וילה), penthouses (נטהאוס), land (קרקע), commercial buildings (בניין), and more. Use get_all_property_type_codes() to see the complete list.',
                    'related_method': 'get_all_property_type_codes()'
                },
                {
                    'question': 'How do I convert between Hebrew and English property type names?',
                    'answer': 'Use the convert_property_type() method with appropriate format parameters. For example: scraper.convert_property_type(1, "yad2", "english") converts code 1 to "Apartment".',
                    'related_method': 'convert_property_type()'
                },
                {
                    'question': 'Can I search for property types by partial names?',
                    'answer': 'Yes! Use search_property_types() with partial text. For example: scraper.search_property_types("דירה") will find all property types containing "דירה".',
                    'related_method': 'search_property_types()'
                },
                {
                    'question': 'How do I get detailed information about a property type?',
                    'answer': 'Use get_property_type_details() with the property type code. This returns comprehensive information including category, description, and translations.',
                    'related_method': 'get_property_type_details()'
                },
                {
                    'question': 'What export formats are supported?',
                    'answer': 'The system supports JSON, CSV, and Excel exports. Use export_codes_to_json(), export_property_types_to_csv(), or export_property_types_to_excel() methods.',
                    'related_methods': ['export_codes_to_json()', 'export_property_types_to_csv()', 'export_property_types_to_excel()']
                },
                {
                    'question': 'How can I compare different property types?',
                    'answer': 'Use compare_property_types() to compare two property types. This method shows similarities, differences, and provides recommendations.',
                    'related_method': 'compare_property_types()'
                },
                {
                    'question': 'Can I get property type recommendations based on criteria?',
                    'answer': 'Yes! Use get_property_type_recommendations() with criteria like budget, family size, location, and investment goals.',
                    'related_method': 'get_property_type_recommendations()'
                },
                {
                    'question': 'How do I validate property type codes?',
                    'answer': 'Use validate_property_type_code() to check if a code is valid. This method returns validation results and suggestions for invalid codes.',
                    'related_method': 'validate_property_type_code()'
                },
                {
                    'question': 'What market analysis features are available?',
                    'answer': 'The system provides market analysis including market position, investment potential, risks, and opportunities for each property type.',
                    'related_method': 'get_property_type_market_analysis()'
                },
                {
                    'question': 'How can I get help and documentation?',
                    'answer': 'Multiple help resources are available: get_property_type_help(), get_property_type_documentation(), get_property_type_examples(), and get_property_type_cheat_sheet().',
                    'related_methods': ['get_property_type_help()', 'get_property_type_documentation()', 'get_property_type_examples()', 'get_property_type_cheat_sheet()']
                }
            ],
            'common_use_cases': [
                {
                    'use_case': 'Building a property search form',
                    'solution': 'Use get_all_property_type_codes() to populate dropdown menus and validate user input with validate_property_type_code().',
                    'methods': ['get_all_property_type_codes()', 'validate_property_type_code()']
                },
                {
                    'use_case': 'Creating multilingual property listings',
                    'solution': 'Use convert_property_type() to display property types in different languages based on user preferences.',
                    'methods': ['convert_property_type()', 'get_property_type_mapping()']
                },
                {
                    'use_case': 'Generating property type reports',
                    'solution': 'Use export methods and analysis functions to create comprehensive reports for clients or internal use.',
                    'methods': ['export_property_types_to_excel()', 'get_property_type_market_analysis()', 'get_property_type_comparison_table()']
                },
                {
                    'use_case': 'Implementing property recommendations',
                    'solution': 'Use get_property_type_recommendations() with user criteria to suggest suitable property types.',
                    'methods': ['get_property_type_recommendations()', 'get_property_type_trends()']
                }
            ]
        }
        
        return faq
    
    def get_property_type_troubleshooting(self):
        """
        Get troubleshooting guide for common property type issues.
        
        Returns:
            Dict containing troubleshooting information
        """
        troubleshooting = {
            'title': 'Yad2 Property Types - Troubleshooting Guide',
            'common_issues': [
                {
                    'issue': 'Property type code not found',
                    'symptoms': ['Error: "Invalid property type code"', 'Method returns None', 'KeyError when accessing property types'],
                    'causes': ['Using outdated property type codes', 'Typo in property type code', 'Code not in the current Yad2 system'],
                    'solutions': [
                        'Use get_all_property_type_codes() to see valid codes',
                        'Validate codes with validate_property_type_code()',
                        'Check for typos or formatting issues',
                        'Update to latest version if codes have changed'
                    ],
                    'prevention': 'Always validate property type codes before use',
                    'related_methods': ['get_all_property_type_codes()', 'validate_property_type_code()']
                },
                {
                    'issue': 'Hebrew text not displaying correctly',
                    'symptoms': ['Garbled Hebrew characters', 'Question marks instead of Hebrew', 'Encoding errors'],
                    'causes': ['Incorrect file encoding', 'Missing Hebrew font support', 'UTF-8 encoding issues'],
                    'solutions': [
                        'Ensure files are saved with UTF-8 encoding',
                        'Use encoding="utf-8" when opening files',
                        'Check system Hebrew font support',
                        'Verify terminal/console encoding settings'
                    ],
                    'prevention': 'Always use UTF-8 encoding for Hebrew text',
                    'related_methods': ['export_codes_to_json()', 'export_property_types_to_csv()']
                },
                {
                    'issue': 'Property type conversion failing',
                    'symptoms': ['convert_property_type() returns None', 'Conversion errors', 'Unexpected results'],
                    'causes': ['Invalid source format', 'Property type not found', 'Format mismatch'],
                    'solutions': [
                        'Verify source and target formats are correct',
                        'Check if property type exists in source format',
                        'Use get_property_type_mapping() to see available conversions',
                        'Validate input before conversion'
                    ],
                    'prevention': 'Validate input formats and use proper error handling',
                    'related_methods': ['convert_property_type()', 'get_property_type_mapping()', 'validate_property_type_code()']
                },
                {
                    'issue': 'Export functions not working',
                    'symptoms': ['File not created', 'Permission errors', 'Import errors'],
                    'causes': ['Missing dependencies', 'File permission issues', 'Invalid file paths'],
                    'solutions': [
                        'Install required dependencies (pandas, openpyxl for Excel)',
                        'Check file permissions and directory access',
                        'Verify file paths are valid',
                        'Ensure sufficient disk space'
                    ],
                    'prevention': 'Install dependencies and test file permissions',
                    'related_methods': ['export_codes_to_json()', 'export_property_types_to_csv()', 'export_property_types_to_excel()']
                },
                {
                    'issue': 'API calls failing',
                    'symptoms': ['Network errors', 'Timeout errors', 'HTTP error codes'],
                    'causes': ['Network connectivity issues', 'Yad2 API changes', 'Rate limiting', 'Invalid API endpoints'],
                    'solutions': [
                        'Check network connectivity',
                        'Verify API endpoints are still valid',
                        'Implement retry logic with delays',
                        'Check for API rate limiting',
                        'Update to latest version for API changes'
                    ],
                    'prevention': 'Implement robust error handling and retry logic',
                    'related_methods': ['fetch_location_data()', 'fetch_property_types()']
                }
            ],
            'debugging_tips': [
                {
                    'tip': 'Use print_codes_summary() for quick debugging',
                    'description': 'This method provides a formatted overview of all property types for quick verification.',
                    'method': 'print_codes_summary()'
                },
                {
                    'tip': 'Check method return values',
                    'description': 'Always verify that methods return expected data types and values.',
                    'example': 'result = scraper.get_all_property_type_codes()\nassert isinstance(result, dict)'
                },
                {
                    'tip': 'Use validation methods',
                    'description': 'Use validate_property_type_code() to check input validity before processing.',
                    'method': 'validate_property_type_code()'
                },
                {
                    'tip': 'Test with known values',
                    'description': 'Test functionality with known valid property type codes (e.g., 1 for דירה).',
                    'example': 'details = scraper.get_property_type_details(1)\nassert details is not None'
                }
            ],
            'performance_optimization': [
                {
                    'tip': 'Cache property type data',
                    'description': 'Store property type data in memory if making multiple calls.',
                    'example': 'all_types = scraper.get_all_property_type_codes()\n# Reuse all_types instead of calling again'
                },
                {
                    'tip': 'Use specific methods',
                    'description': 'Use specific methods instead of comprehensive ones when possible.',
                    'example': 'Use get_property_type_details(1) instead of get_comprehensive_property_info()'
                },
                {
                    'tip': 'Batch operations',
                    'description': 'Group related operations together to minimize overhead.',
                    'example': 'Export all data at once instead of multiple individual exports'
                }
            ],
            'error_recovery': [
                {
                    'strategy': 'Graceful degradation',
                    'description': 'Provide fallback values when property type data is unavailable.',
                    'example': 'details = scraper.get_property_type_details(code) or {"name": "Unknown", "category": "Other"}'
                },
                {
                    'strategy': 'Retry logic',
                    'description': 'Implement retry mechanisms for transient failures.',
                    'example': 'for attempt in range(3):\n    try:\n        result = method()\n        break\n    except Exception:\n        time.sleep(1)'
                },
                {
                    'strategy': 'User feedback',
                    'description': 'Provide clear error messages and suggestions to users.',
                    'example': 'if not result:\n    print("Property type not found. Use get_all_property_type_codes() to see available options.")'
                }
            ]
        }
        
        return troubleshooting
    
    def set_search_parameters(self, **kwargs):
        """Set or update search parameters."""
        for key, value in kwargs.items():
            try:
                self.search_params.set_parameter(key, value)
            except ValueError as e:
                print("Warning: {}".format(e))
    
    def build_search_url(self, page=1):
        """Build the search URL with current parameters."""
        # Set page parameter
        self.search_params.set_parameter('page', page)
        
        # Build URL with all parameters
        base_url = self.base_url + self.search_endpoint
        return self.search_params.build_url(base_url)
    
    def fetch_page(self, url, retries=3, delay=1):
        """
        Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            delay: Delay between retries in seconds
        
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                elif response.status_code == 429:  # Rate limited
                    print("Rate limited, waiting {} seconds...".format(delay * (attempt + 1)))
                    time.sleep(delay * (attempt + 1))
                else:
                    print("Failed to fetch page: {}".format(response.status_code))
                    
            except requests.exceptions.RequestException as e:
                print("Error fetching page (attempt {}): {}".format(attempt + 1, e))
                if attempt < retries - 1:
                    time.sleep(delay)
        
        return None
    
    def extract_listing_info(self, listing_element):
        """
        Extract information from a listing element using working selectors.
        
        Args:
            listing_element: BeautifulSoup element containing listing data
            
        Returns:
            RealEstateListing object or None
        """
        try:
            listing = RealEstateListing()
            
            # Extract price using working selector
            price_elem = listing_element.select_one('[data-testid="price"]')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                listing.price = URLUtils.clean_price(price_text)
            
            # Extract title/address using working selector
            title_elem = listing_element.select_one("span.item-data-content_heading__tphH4")
            if title_elem:
                listing.title = title_elem.get_text(strip=True)
                listing.address = title_elem.get_text(strip=True)
            
            # Extract property details using working selector
            desc_lines = listing_element.select("span.item-data-content_itemInfoLine__AeoPP")
            if len(desc_lines) > 1:
                values = desc_lines[1].get_text(strip=True).split(' • ')
                if len(values) >= 1:
                    listing.rooms = URLUtils.extract_number(values[0])
                if len(values) >= 2:
                    listing.floor = values[1].strip()
                if len(values) >= 3:
                    listing.size = URLUtils.extract_number(values[2])
            
            # Extract URL
            link_elem = listing_element.find('a', href=True)
            if link_elem:
                listing.url = urljoin(self.base_url, link_elem['href'])
                listing.listing_id = URLUtils.extract_listing_id(listing.url)
            
            return listing
            
        except Exception as e:
            print("Error extracting listing info: {}".format(e))
            return None
    
    def scrape_page(self, page=1):
        """
        Scrape a single page of listings.
        
        Args:
            page: Page number to scrape
            
        Returns:
            List of RealEstateListing objects
        """
        url = self.build_search_url(page)
        print("Scraping page {} from: {}".format(page, url))
        
        soup = self.fetch_page(url)
        if not soup:
            print("Failed to fetch page {}".format(page))
            return []
        
        # Use the working selector from utils
        items = soup.select("a.item-layout_itemLink__CZZ7w")
        if not items:
            print("No listings found on page {} - trying fallback extraction".format(page))
            return []
        
        print("Found {} listings using working selector".format(len(items)))
        
        listings = []
        for item in items:
            # Find the parent card container
            card = item.find_parent("div", class_="card_cardBox__KLi9I")
            if card:
                listing = self.extract_listing_info(card)
                if listing and listing.title:  # Only add if we got meaningful data
                    listings.append(listing)
        
        return listings
    
    def scrape_all_pages(self, max_pages=10, delay=2):
        """
        Scrape multiple pages of listings.
        
        Args:
            max_pages: Maximum number of pages to scrape
            delay: Delay between page requests in seconds
            
        Returns:
            List of all RealEstateListing objects
        """
        all_listings = []
        
        for page in range(1, max_pages + 1):
            try:
                listings = self.scrape_page(page)
                
                if not listings:
                    print("No more listings found on page {}".format(page))
                    break
                
                all_listings.extend(listings)
                print("Page {}: Found {} listings (Total: {})".format(
                    page, len(listings), len(all_listings)))
                
                # Add delay between requests to be respectful
                if page < max_pages:
                    time.sleep(delay)
                    
            except KeyboardInterrupt:
                print("Scraping interrupted by user")
                break
            except Exception as e:
                print("Error scraping page {}: {}".format(page, e))
                continue
        
        self.listings = all_listings
        return all_listings
    
    def get_search_summary(self):
        """Get a summary of the current search parameters."""
        active_params = self.search_params.get_active_parameters()
        
        summary = {
            'search_url': self.build_search_url(1),
            'parameters': active_params,
            'parameter_descriptions': {}
        }
        
        # Add human-readable descriptions for parameters
        for param, value in active_params.items():
            info = self.param_reference.get_parameter_info(param)
            summary['parameter_descriptions'][param] = {
                'value': value,
                'description': info['description']
            }
            
            # Add property type names if applicable
            if param == 'property' and value:
                prop_types = str(value).split(',')
                type_names = []
                for prop_id in prop_types:
                    try:
                        type_name = self.param_reference.get_property_types().get(int(prop_id.strip()))
                        if type_name:
                            type_names.append(type_name)
                    except (ValueError, TypeError):
                        pass
                if type_names:
                    summary['parameter_descriptions'][param]['type_names'] = type_names
        
        return summary
    
    def save_to_json(self, filename=None):
        """Save listings to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "yad2_listings_{}.json".format(timestamp)
        
        data = {
            'search_summary': self.get_search_summary(),
            'scrape_time': datetime.now().isoformat(),
            'total_listings': len(self.listings),
            'listings': [listing.to_dict() for listing in self.listings]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("Saved {} listings to {}".format(len(self.listings), filename))
        return filename
    
    @classmethod
    def from_url(cls, url, **kwargs):
        """
        Create scraper from existing Yad2 URL.
        
        Args:
            url: Yad2 URL with parameters
            **kwargs: Additional scraper options
            
        Returns:
            Yad2Scraper instance
        """
        params_dict = URLUtils.extract_url_parameters(url)
        return cls(search_params=params_dict, **kwargs) 