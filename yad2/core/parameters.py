#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Search Parameters

Comprehensive parameter system for Yad2 real estate searches.
"""

import json
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


class Yad2SearchParameters:
    """
    Comprehensive data class for Yad2 search parameters.
    """
    
    def __init__(self, **kwargs):
        # Initialize all known parameters
        self.parameters = {
            # Price parameters
            'maxPrice': None,
            'minPrice': None,
            
            # Property type parameters
            'property': None,  # Comma-separated property type IDs
            
            # Location parameters
            'topArea': None,      # Regional area (1=North, 2=Center, 3=South, etc.)
            'area': None,         # Sub-area within region
            'city': None,         # City ID
            'neighborhood': None, # Neighborhood ID
            'street': None,       # Street name
            
            # Property details
            'rooms': None,        # Number of rooms (e.g., "3-4", "4+")
            'floor': None,        # Floor range (e.g., "1-3", "4+")
            'size': None,         # Property size in sqm
            'minSize': None,      # Minimum size
            'maxSize': None,      # Maximum size
            
            # Features
            'parking': None,      # Number of parking spaces
            'elevator': None,     # Has elevator (1/0)
            'balcony': None,      # Has balcony (1/0)
            'renovated': None,    # Is renovated (1/0)
            'accessibility': None, # Accessibility features (1/0)
            'airCondition': None, # Has air conditioning (1/0)
            'bars': None,         # Has security bars (1/0)
            'mamad': None,        # Has safe room (1/0)
            'storage': None,      # Has storage (1/0)
            'terrace': None,      # Has terrace (1/0)
            'garden': None,       # Has garden (1/0)
            'pets': None,         # Pets allowed (1/0)
            'furniture': None,    # Is furnished (1/0)
            
            # Building details
            'buildingFloors': None,   # Total building floors
            'entranceDate': None,     # Move-in date
            'propertyCondition': None, # Property condition
            
            # Search parameters
            'page': None,         # Page number
            'order': None,        # Sort order
            'dealType': None,     # Deal type (sale/rent)
            'priceOnly': None,    # Show price only listings (1/0)
            'saleType': None,     # Sale type
            'exclusive': None,    # Exclusive listings only (1/0)
            'publishedDays': None, # Published within X days
            
            # Advanced filters
            'fromFloor': None,    # From floor
            'toFloor': None,      # To floor
            'yearBuilt': None,    # Year built
            'minYear': None,      # Minimum year built
            'maxYear': None,      # Maximum year built
        }
        
        # Update with provided kwargs
        for key, value in kwargs.items():
            if key in self.parameters:
                self.parameters[key] = value
    
    def set_parameter(self, key, value):
        """Set a parameter value with validation."""
        if key in self.parameters:
            # Basic validation
            if value is not None and value != '':
                if key in ['maxPrice', 'minPrice', 'topArea', 'area', 'city', 'neighborhood', 
                          'parking', 'minSize', 'maxSize', 'buildingFloors', 'fromFloor', 
                          'toFloor', 'yearBuilt', 'minYear', 'maxYear', 'page']:
                    try:
                        self.parameters[key] = int(value)
                    except ValueError:
                        raise ValueError("Parameter '{}' must be a number".format(key))
                elif key in ['elevator', 'balcony', 'renovated', 'accessibility', 
                           'airCondition', 'bars', 'mamad', 'storage', 'terrace', 
                           'garden', 'pets', 'furniture', 'priceOnly', 'exclusive']:
                    # Boolean parameters
                    if str(value).lower() in ['true', '1', 'yes', 'y']:
                        self.parameters[key] = 1
                    elif str(value).lower() in ['false', '0', 'no', 'n']:
                        self.parameters[key] = 0
                    else:
                        self.parameters[key] = int(value)  # Allow direct 1/0
                else:
                    self.parameters[key] = str(value)
            else:
                self.parameters[key] = None
        else:
            raise ValueError("Unknown parameter: {}".format(key))
    
    def get_active_parameters(self):
        """Get only parameters that have values."""
        return {k: v for k, v in self.parameters.items() if v is not None}
    
    def to_dict(self):
        """Convert to dictionary."""
        return self.get_active_parameters()
    
    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.get_active_parameters(), indent=2)
    
    def build_url(self, base_url="https://www.yad2.co.il/realestate/forsale"):
        """Build complete Yad2 URL with parameters."""
        active_params = self.get_active_parameters()
        if active_params:
            return "{}?{}".format(base_url, urlencode(active_params))
        return base_url


class Yad2ParameterReference:
    """
    Reference guide for Yad2 parameters with descriptions and examples.
    """
    
    PARAMETER_INFO = {
        'maxPrice': {
            'description': 'Maximum price in NIS',
            'example': 5000000,
            'type': 'integer'
        },
        'minPrice': {
            'description': 'Minimum price in NIS',
            'example': 2000000,
            'type': 'integer'
        },
        'property': {
            'description': 'Property types (comma-separated IDs)',
            'example': 1,
            'type': 'string',
            'options': {
                1: 'Apartment',
                2: 'House/Villa',
                5: 'Duplex',
                6: 'Plot/Land',
                15: 'Building',
                33: 'Penthouse',
                39: 'Studio',
                31: 'Loft',
                32: 'Triplex',
                34: 'Garden Apartment',
                35: 'Rooftop',
                36: 'Unit',
                37: 'Mini Penthouse'
            }
        },
        'topArea': {
            'description': 'Regional area',
            'example': 2,
            'type': 'integer',
            'options': {
                1: 'North',
                2: 'Center', 
                3: 'South',
                4: 'Jerusalem Area',
                5: 'West Bank'
            }
        },
        'area': {
            'description': 'Sub-area within region (1=TLV, 3=RamatGan,Givataim)',
            'example': 1,
            'type': 'integer',
            'options': {
                1: 'Tel Aviv',
                3: 'Ramat Gan, Givatayim'
            }
        },
        'city': {
            'description': 'City ID',
            'example': 5000,
            'type': 'integer',
            'options': {
                5000: 'Tel Aviv',
                6200: 'Jerusalem',
                6300: 'Haifa'
            }
        },
        'neighborhood': {
            'description': 'Neighborhood ID within city (e.g., 203=Ramat HaHayal)',
            'example': 203,
            'type': 'integer',
            'options': {
                203: 'Ramat HaHayal',
                199: 'City Center',
                200: 'Neve Tzedek',
                312: 'Florentin'
            }
        },
        'rooms': {
            'description': 'Number of rooms',
            'example': '3-4, 4+, 2.5-3.5',
            'type': 'string'
        },
        'floor': {
            'description': 'Floor range',
            'example': '1-3, 4+, 0 (ground)',
            'type': 'string'
        },
        'size': {
            'description': 'Property size in square meters',
            'example': '80-120',
            'type': 'string'
        },
        'minSize': {
            'description': 'Minimum size in square meters',
            'example': 80,
            'type': 'integer'
        },
        'maxSize': {
            'description': 'Maximum size in square meters',
            'example': 120,
            'type': 'integer'
        },
        'parking': {
            'description': 'Number of parking spaces',
            'example': 1,
            'type': 'integer'
        },
        'elevator': {
            'description': 'Has elevator',
            'example': '1 (yes), 0 (no)',
            'type': 'boolean'
        },
        'balcony': {
            'description': 'Has balcony',
            'example': '1 (yes), 0 (no)',
            'type': 'boolean'
        },
        'renovated': {
            'description': 'Is renovated',
            'example': '1 (yes), 0 (no)',
            'type': 'boolean'
        },
        'order': {
            'description': 'Sort order',
            'example': 'date, price_asc, price_desc, size_asc, size_desc',
            'type': 'string',
            'options': {
                'date': 'By date (newest first)',
                'price_asc': 'Price low to high',
                'price_desc': 'Price high to low', 
                'size_asc': 'Size small to large',
                'size_desc': 'Size large to small'
            }
        }
    }
    
    @classmethod
    def get_parameter_info(cls, param_name):
        """Get information about a specific parameter."""
        return cls.PARAMETER_INFO.get(param_name, {'description': 'Unknown parameter', 'example': '', 'type': 'string'})
    
    @classmethod
    def list_all_parameters(cls):
        """List all available parameters with descriptions."""
        return cls.PARAMETER_INFO
    
    @classmethod
    def get_property_types(cls):
        """Get all property type options."""
        return cls.PARAMETER_INFO['property']['options'] 