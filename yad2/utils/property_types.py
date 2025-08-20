#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property Types Utility Module

Clean, focused property type functionality extracted from the main scraper.
"""

from datetime import datetime
import json
import csv


class PropertyTypeUtils:
    """Utility class for property type operations."""
    
    @staticmethod
    def translate_to_english(hebrew_name):
        """Translate Hebrew property type names to English."""
        translations = {
            'דירה': 'Apartment',
            'דירה עם גינה': 'Apartment with Garden',
            'קוטג': 'Cottage',
            'וילה': 'Cottage',
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
    
    @staticmethod
    def hebrew_name_to_code(hebrew_name):
        """Convert Hebrew property type names to Yad2 codes."""
        hebrew_to_code = {
            # Main property types - matching official parameters.py
            'דירה': 1,                    # Apartment
            'דירה עם גינה': 3,            # Apartment with Garden
            'נטהאוס': 6,                  # Penthouse
            'דופלקס': 7,                  # Duplex
            'מלון': 25,                   # Hotel
            'מרתף': 49,                   # Basement
            'טריפלקס': 51,                # Triplex
            'דירה משנית': 11,             # Sub-apartment
            'סטודיו': 4,                  # Studio
            'קוטג': 5,                    # Cottage
            'וילה': 5,                    # Cottage (synonym)
            'בית דו משפחתי': 39,          # Two-family house
            'משק חקלאי': 32,              # Agricultural farm
            'חצר': 52,                    # Farm
            'קרקע': 33,                   # Land
            'בית בטוח': 61,               # Safe house
            'ממ"ד': 61,                   # Safe house (synonym)
            'בניין': 44,                  # Building
            'גראז': 45,                   # Garage
            'חניה': 30,                   # Parking
            'דירה עתידית': 50,            # Future apartment
            
            # Additional Hebrew names for better coverage
            'בית פרטי': 39,               # Two-family house (same as בית דו משפחתי)
            'בית': 39,                    # Two-family house (same as בית דו משפחתי)
            'דירת גן': 3,                 # Apartment with Garden (same as דירה עם גינה)
            'גג': 6,                      # Penthouse (same as נטהאוס)
            'יחידה': 1,                   # Apartment (same as דירה)
            'מיני פנטהאוס': 6,           # Penthouse (same as נטהאוס)
            'לופט': 7,                    # Duplex (same as דופלקס)
            'דירת נופש': 25,              # Hotel (same as מלון)
            'בית מלון': 25,               # Hotel (same as מלון)
            'מרחב מוגן דירתי': 61,       # Safe house (same as ממ"ד)
        }
        return hebrew_to_code.get(hebrew_name, None)
    
    @staticmethod
    def english_name_to_code(english_name):
        """Convert English property type names to Yad2 codes."""
        english_to_code = {
            # Main property types - matching official parameters.py
            'apartment': 1,               # דירה
            'apartment with garden': 3,   # דירה עם גינה
            'penthouse': 6,               # נטהאוס
            'duplex': 7,                  # דופלקס
            'hotel': 25,                  # מלון
            'basement': 49,               # מרתף
            'triplex': 51,                # טריפלקס
            'sub-apartment': 11,          # דירה משנית
            'studio': 4,                  # סטודיו
            'cottage': 5,                 # קוטג
            'villa': 5,                   # קוטג (synonym)
            'two-family house': 39,       # בית דו משפחתי
            'agricultural farm': 32,      # משק חקלאי
            'farm': 52,                   # חצר
            'land': 33,                   # קרקע
            'safe house': 61,             # בית בטוח
            'protected space': 61,        # ממ"ד
            'building': 44,               # בניין
            'garage': 45,                 # גראז
            'parking': 30,                # חניה
            'future apartment': 50,       # דירה עתידית
            
            # Additional English names for better coverage
            'house': 39,                  # Two-family house
            'private house': 39,          # Two-family house
            'single-family house': 39,    # Two-family house
            'garden apartment': 3,        # Apartment with Garden
            'rooftop': 6,                 # Penthouse
            'unit': 1,                    # Apartment
            'mini penthouse': 6,          # Penthouse
            'loft': 7,                    # Duplex
            'vacation apartment': 25,     # Hotel
            'mamad': 61,                  # Safe house
        }
        return english_to_code.get(english_name.lower(), None)
    
    @staticmethod
    def search_hebrew_name_to_code(search_term):
        """Search for Hebrew property type names and return matching codes."""
        hebrew_to_code = {
            'דירה': 1,
            'דירה עם גינה': 3,
            'נטהאוס': 6,
            'דופלקס': 7,
            'קוטג': 5,  # Updated: קוטג instead of וילה
            'וילה': 5,  # Keep for backward compatibility
            'בית': 39,  # Fixed: בית should be Single-family house (39), not Villa (5)
            'בית פרטי': 39,  # Fixed: בית פרטי should be Single-family house (39), not Villa (5)
            'בית דו משפחתי': 39,  # Fixed: בית דו משפחתי should be Two-family house (39)
            'בית דו-משפחתי': 39,  # Fixed: בית דו-משפחתי should be Two-family house (39)
            'דו משפחתי': 39,  # Fixed: דו משפחתי should be Two-family house (39)
            'דו-משפחתי': 39,  # Fixed: דו-משפחתי should be Two-family house (39)
            'קרקע': 33,
            'בניין': 44,
            'גראז': 45,
            'חניה': 30,
            'דירה עתידית': 50,
            'דירת גן': 34,
            'גג': 35,
            'יחידה': 36,
            'מיני פנטהאוס': 37,
            'טריפלקס': 32,
            'לופט': 31,
            'מלון': 25,
            'מרתף': 49,
            'דירת נופש': 25,
            'בית מלון': 25,
            'חצר': 52,
            'משק חקלאי': 32,
            'בית בטוח': 61,
            'ממ"ד': 61,
            'מרחב מוגן דירתי': 61
        }
        
        # Search for partial matches
        matching_codes = []
        search_term_lower = search_term.lower()
        
        for hebrew_name, code in hebrew_to_code.items():
            if search_term_lower in hebrew_name.lower() or hebrew_name.lower() in search_term_lower:
                matching_codes.append((code, hebrew_name))
        
        return matching_codes
    
    @staticmethod
    def categorize_property_type(code):
        """Categorize property types into main categories."""
        residential = [1, 3, 5, 6, 31, 32, 34, 35, 36, 37, 39]
        commercial = [15]
        land = [33]
        
        if code in residential:
            return 'Residential'
        elif code in commercial:
            return 'Commercial'
        elif code in land:
            return 'Land'
        else:
            return 'Other'
    
    @staticmethod
    def get_description(code):
        """Get detailed description for property type."""
        descriptions = {
            1: 'Standard apartment unit in a residential building',
            3: 'Apartment with private garden or outdoor space',
            5: 'Cottage - small detached house with private land',
            6: 'Luxury apartment on the top floor of a building',
            15: 'Commercial building or structure',
            33: 'Vacant land for development',
            31: 'Open-concept living space, often in converted industrial buildings',
            32: 'Three-level apartment or house',
            34: 'Ground floor apartment with garden access',
            35: 'Apartment or unit on the roof of a building',
            36: 'Individual unit in a larger complex',
            37: 'Smaller version of a penthouse',
            39: 'Two-family house or duplex'
        }
        return descriptions.get(code, 'No description available')
    
    @staticmethod
    def get_aliases():
        """Get common aliases and alternative names for property types."""
        return {
            'דירה': ['apartment', 'flat', 'unit', 'condo'],
            'דירה עם גינה': ['garden apartment', 'apartment with garden', 'ground floor apartment'],
            'קוטג': ['cottage', 'small house', 'country house', 'holiday home'],
            'וילה': ['cottage', 'small house', 'country house', 'holiday home'],
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
    
    @staticmethod
    def export_to_json(property_types, filename=None):
        """Export property types to JSON format."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"property_types_{timestamp}.json"
        
        data = {
            'export_time': datetime.now().isoformat(),
            'total_count': len(property_types),
            'property_types': property_types
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    @staticmethod
    def export_to_csv(property_types, filename=None):
        """Export property types to CSV format."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"property_types_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['code', 'name_hebrew', 'name_english', 'category', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for code, hebrew_name in property_types.items():
                writer.writerow({
                    'code': code,
                    'name_hebrew': hebrew_name,
                    'name_english': PropertyTypeUtils.translate_to_english(hebrew_name),
                    'category': PropertyTypeUtils.categorize_property_type(code),
                    'description': PropertyTypeUtils.get_description(code)
                })
        
        return filename
    
    @staticmethod
    def export_to_excel(property_types, filename=None):
        """Export property types to Excel format."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"property_types_{timestamp}.xlsx"
        
        try:
            import pandas as pd
            
            data = []
            for code, hebrew_name in property_types.items():
                data.append({
                    'Code': code,
                    'Name (Hebrew)': hebrew_name,
                    'Name (English)': PropertyTypeUtils.translate_to_english(hebrew_name),
                    'Category': PropertyTypeUtils.categorize_property_type(code),
                    'Description': PropertyTypeUtils.get_description(code),
                    'Aliases': ', '.join(PropertyTypeUtils.get_aliases().get(hebrew_name, []))
                })
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, sheet_name='Property Types')
            
            return filename
            
        except ImportError:
            print("pandas is required for Excel export. Install with: pip install pandas openpyxl")
            return None
    
    @staticmethod
    def print_summary(property_types):
        """Print a formatted summary of property types to console."""
        print("=" * 60)
        print("YAD2 PROPERTY TYPES SUMMARY")
        print("=" * 60)
        
        for code, name in property_types.items():
            english_name = PropertyTypeUtils.translate_to_english(name)
            category = PropertyTypeUtils.categorize_property_type(code)
            print(f"  {code:2d}: {name} ({english_name}) - {category}")
        
        print(f"\nTotal: {len(property_types)} property types")
        print("=" * 60)

    @staticmethod
    def get_correct_property_codes():
        """Get the correct Yad2 property type codes with explanations.
        
        This method returns the official Yad2 codes that match the parameters.py file.
        """
        return {
            'דירה': {'code': 1, 'english': 'Apartment', 'description': 'דירה רגילה'},
            'דירה עם גינה': {'code': 3, 'english': 'Apartment with Garden', 'description': 'דירה עם גינה'},
            'קוטג': {'code': 5, 'english': 'Cottage', 'description': 'קוטג'},
            'וילה': {'code': 5, 'english': 'Cottage', 'description': 'וילה - קוטג'},
            'בית פרטי': {'code': 39, 'english': 'Single-family house', 'description': 'בית פרטי - בית חד משפחתי'},
            'בית': {'code': 39, 'english': 'Single-family house', 'description': 'בית - בית חד משפחתי'},
            'נטהאוס': {'code': 6, 'english': 'Penthouse', 'description': 'נטהאוס'},
            'דופלקס': {'code': 7, 'english': 'Duplex', 'description': 'דופלקס'},
            'בית דו משפחתי': {'code': 39, 'english': 'Two-family house', 'description': 'בית דו משפחתי'},
            'בית דו-משפחתי': {'code': 39, 'english': 'Two-family house', 'description': 'בית דו-משפחתי'},
            'דו משפחתי': {'code': 39, 'english': 'Two-family house', 'description': 'דו משפחתי'},
            'דו-משפחתי': {'code': 39, 'english': 'Two-family house', 'description': 'דו-משפחתי'},
            'קרקע': {'code': 33, 'english': 'Land', 'description': 'קרקע לבנייה'},
            'בניין': {'code': 44, 'english': 'Building', 'description': 'בניין שלם'},
            'גראז': {'code': 45, 'english': 'Garage', 'description': 'חניה/גראז'},
            'חניה': {'code': 30, 'english': 'Parking', 'description': 'חניה'},
            'דירה עתידית': {'code': 50, 'english': 'Future apartment', 'description': 'דירה עתידית'},
            'דירת גן': {'code': 34, 'english': 'Garden Apartment', 'description': 'דירת גן'},
            'גג': {'code': 35, 'english': 'Rooftop', 'description': 'גג'},
            'יחידה': {'code': 36, 'english': 'Unit', 'description': 'יחידה'},
            'מיני פנטהאוס': {'code': 37, 'english': 'Mini Penthouse', 'description': 'מיני פנטהאוס'},
            'טריפלקס': {'code': 32, 'english': 'Triplex', 'description': 'טריפלקס'},
            'לופט': {'code': 31, 'english': 'Loft', 'description': 'לופט'},
            'מלון': {'code': 25, 'english': 'Hotel', 'description': 'מלון'},
            'מרתף': {'code': 49, 'english': 'Basement', 'description': 'מרתף'},
            'דירת נופש': {'code': 25, 'english': 'Vacation apartment', 'description': 'דירת נופש'},
            'בית מלון': {'code': 25, 'english': 'Hotel', 'description': 'בית מלון'},
            'חצר': {'code': 52, 'english': 'Farm', 'description': 'חצר/משק'},
            'משק חקלאי': {'code': 32, 'english': 'Agricultural farm', 'description': 'משק חקלאי'},
            'בית בטוח': {'code': 61, 'english': 'Safe house', 'description': 'בית בטוח/ממ"ד'},
            'ממ"ד': {'code': 61, 'english': 'Safe house', 'description': 'מרחב מוגן דירתי'},
            'מרחב מוגן דירתי': {'code': 61, 'english': 'Safe house', 'description': 'מרחב מוגן דירתי'}
        }

    @staticmethod
    def get_correct_neighborhood_codes():
        """Get the correct Yad2 neighborhood codes for Tel Aviv.
        
        This method returns the official Yad2 codes that match the parameters.py file.
        """
        return {
            'רמת החייל': {'code': 203, 'english': 'Ramat HaHayal', 'description': 'שכונת רמת החייל בתל אביב'},
            'מרכז העיר': {'code': 199, 'english': 'City Center', 'description': 'מרכז העיר תל אביב'},
            'נווה צדק': {'code': 200, 'english': 'Neve Tzedek', 'description': 'שכונת נווה צדק'},
            'פלורנטין': {'code': 312, 'english': 'Florentin', 'description': 'שכונת פלורנטין'},
            'תל אביב': {'code': 5000, 'english': 'Tel Aviv', 'description': 'עיר תל אביב'},
            'ירושלים': {'code': 6200, 'english': 'Jerusalem', 'description': 'עיר ירושלים'},
            'חיפה': {'code': 6300, 'english': 'Haifa', 'description': 'עיר חיפה'}
        }

    @staticmethod
    def print_correct_codes():
        """Print the correct property type and neighborhood codes for verification.
        
        This method helps developers and users verify that they're using the right codes.
        """
        print("=" * 60)
        print("YAD2 PROPERTY TYPE CODES (CORRECTED)")
        print("=" * 60)
        
        property_codes = PropertyTypeUtils.get_correct_property_codes()
        for hebrew_name, info in property_codes.items():
            print(f"{hebrew_name:20} -> Code: {info['code']:2} | {info['english']:25} | {info['description']}")
        
        print("\n" + "=" * 60)
        print("YAD2 NEIGHBORHOOD CODES (TEL AVIV)")
        print("=" * 60)
        
        neighborhood_codes = PropertyTypeUtils.get_correct_neighborhood_codes()
        for hebrew_name, info in neighborhood_codes.items():
            print(f"{hebrew_name:20} -> Code: {info['code']:4} | {info['english']:25} | {info['description']}")
        
        print("\n" + "=" * 60)
        print("IMPORTANT: Always use these codes for accurate Yad2 searches!")
        print("=" * 60)
