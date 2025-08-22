#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive CLI

Interactive command-line interface for building Yad2 searches.
"""

import json
from ..core import Yad2SearchParameters, Yad2ParameterReference, URLUtils
from ..scrapers import Yad2Scraper


class InteractiveCLI:
    """Interactive command-line interface for Yad2 searches."""
    
    def __init__(self):
        self.parameters = Yad2SearchParameters()
        self.reference = Yad2ParameterReference()
    
    def quick_search(self):
        """Quick search builder for common parameters."""
        print("🚀 Quick Yad2 Search Builder")
        print("=" * 40)
        print("Fill in the parameters you want (press Enter to skip any):")
        print()
        
        params = Yad2SearchParameters()
        
        try:
            # Price range
            max_price = input("Maximum price (NIS): ").strip()
            if max_price:
                params.set_parameter('maxPrice', max_price)
            
            min_price = input("Minimum price (NIS): ").strip()
            if min_price:
                params.set_parameter('minPrice', min_price)
            
            # Location
            print("\nLocation (see reference for common IDs):")
            print("  topArea: 1=North, 2=Center, 3=South, 4=Jerusalem")
            print("  city: 5000=Tel Aviv, 6200=Jerusalem, 6300=Haifa")
            
            top_area = input("Top Area (1-5): ").strip()
            if top_area:
                params.set_parameter('topArea', top_area)
            
            area = input("Area ID: ").strip()
            if area:
                params.set_parameter('area', area)
            
            city = input("City ID: ").strip()
            if city:
                params.set_parameter('city', city)
            
            neighborhood = input("Neighborhood ID: ").strip()
            if neighborhood:
                params.set_parameter('neighborhood', neighborhood)
            
            # Property details
            print("\nProperty Details:")
            print("  property types: 1=Apartment, 5=Duplex, 33=Penthouse, 39=Studio")
            property_types = input("Property types (comma-separated): ").strip()
            if property_types:
                params.set_parameter('property', property_types)
            
            rooms = input("Number of rooms (e.g., 3-4, 4+): ").strip()
            if rooms:
                params.set_parameter('rooms', rooms)
            
            # Features
            print("\nFeatures (enter 1 for yes, 0 for no):")
            parking = input("Parking required (1/0): ").strip()
            if parking:
                params.set_parameter('parking', parking)
            
            elevator = input("Elevator required (1/0): ").strip()
            if elevator:
                params.set_parameter('elevator', elevator)
            
            balcony = input("Balcony required (1/0): ").strip()
            if balcony:
                params.set_parameter('balcony', balcony)
            
            renovated = input("Must be renovated (1/0): ").strip()
            if renovated:
                params.set_parameter('renovated', renovated)
            
            print("\n" + "="*50)
            print("📋 Your Search Parameters:")
            print(params.to_json())
            
            print("\n🔗 Generated Yad2 URL:")
            print(params.build_url())
            print()
            
            return params
            
        except KeyboardInterrupt:
            print("\n\n👋 Search cancelled!")
            return None
        except ValueError as e:
            print("\n❌ Error: {}".format(e))
            return None
    
    def advanced_search(self):
        """Advanced interactive search builder."""
        print("🔧 Advanced Yad2 Search Builder")
        print("=" * 40)
        print("This mode gives you access to all available parameters.")
        print("Type 'help' for parameter reference")
        print()
        
        while True:
            try:
                command = input("Enter parameter name (or command): ").strip()
                
                if command.lower() == 'done':
                    break
                elif command.lower() == 'help':
                    self._show_help()
                elif command.lower() == 'clear':
                    self.parameters = Yad2SearchParameters()
                    print("✅ Parameters cleared!")
                elif command.lower() == 'show':
                    self._show_current_parameters()
                elif command.lower() == 'url':
                    self._show_url()
                elif command == '':
                    continue
                else:
                    self._handle_parameter_input(command)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print("❌ Error: {}".format(e))
        
        return self.parameters
    
    def _show_help(self):
        """Show parameter reference."""
        print("\n📖 Parameter Reference:")
        print("-" * 30)
        
        categories = {
            'Price': ['maxPrice', 'minPrice'],
            'Location': ['topArea', 'area', 'city', 'neighborhood'],
            'Property': ['property', 'rooms', 'size', 'minSize', 'maxSize'],
            'Features': ['parking', 'elevator', 'balcony', 'renovated'],
            'Other': ['floor', 'order']
        }
        
        for category, params in categories.items():
            print("\n{}:".format(category))
            for param in params:
                info = self.reference.get_parameter_info(param)
                print("  {}: {}".format(param, info['description']))
                if info.get('options'):
                    print("    Options: {}".format(list(info['options'].keys())))
                print("    Example: {}".format(info['example']))
        
        print("\nCommands:")
        print("  help  - Show this help")
        print("  show  - Show current parameters")
        print("  url   - Show generated URL")
        print("  clear - Clear all parameters")
        print("  done  - Finish and generate URL")
        print()
    
    def _show_current_parameters(self):
        """Show currently set parameters."""
        active = self.parameters.get_active_parameters()
        if active:
            print("\n📋 Current Parameters:")
            print("-" * 25)
            for key, value in active.items():
                info = self.reference.get_parameter_info(key)
                print("  {}: {} ({})".format(key, value, info['description']))
        else:
            print("\n📋 No parameters set yet.")
        print()
    
    def _show_url(self):
        """Show generated URL."""
        url = self.parameters.build_url()
        print("\n🔗 Generated URL:")
        print(url)
        print()
    
    def _handle_parameter_input(self, param_name):
        """Handle input for a specific parameter."""
        if param_name not in self.reference.PARAMETER_INFO:
            print("❓ Unknown parameter '{}'. Type 'help' for available parameters.".format(param_name))
            return
        
        info = self.reference.get_parameter_info(param_name)
        print("\n🔧 Setting {}".format(param_name))
        print("Description: {}".format(info['description']))
        print("Example: {}".format(info['example']))
        
        if info.get('options'):
            print("Available options:")
            for key, desc in info['options'].items():
                print("  {}: {}".format(key, desc))
        
        value = input("Enter value for {} (or press Enter to skip): ".format(param_name)).strip()
        
        if value:
            try:
                self.parameters.set_parameter(param_name, value)
                print("✅ Set {} = {}".format(param_name, value))
            except ValueError as e:
                print("❌ {}".format(e))
        print()
    
    def show_parameter_reference(self):
        """Show comprehensive parameter reference."""
        print("📖 Yad2 Parameter Reference Guide")
        print("=" * 50)
        
        ref = Yad2ParameterReference()
        params = ref.list_all_parameters()
        
        categories = {
            'Price Parameters': ['maxPrice', 'minPrice'],
            'Location Parameters': ['topArea', 'area', 'city', 'neighborhood', 'street'],
            'Property Types': ['property'],
            'Property Details': ['rooms', 'floor', 'size', 'minSize', 'maxSize'],
            'Features & Amenities': [
                'parking', 'elevator', 'balcony', 'renovated', 'accessibility',
                'airCondition', 'bars', 'mamad', 'storage', 'terrace', 'garden',
                'pets', 'furniture'
            ],
            'Building Details': ['buildingFloors', 'entranceDate', 'propertyCondition'],
            'Search Options': ['page', 'order', 'dealType', 'priceOnly', 'exclusive', 'publishedDays'],
            'Advanced Filters': ['fromFloor', 'toFloor', 'yearBuilt', 'minYear', 'maxYear']
        }
        
        for category, param_list in categories.items():
            print("\n{}:".format(category))
            print("-" * len(category))
            
            for param in param_list:
                if param in params:
                    info = params[param]
                    print("\n  {}".format(param))
                    print("    Description: {}".format(info['description']))
                    print("    Type: {}".format(info['type']))
                    print("    Example: {}".format(info['example']))
                    
                    if info.get('options'):
                        print("    Options:")
                        for key, desc in info['options'].items():
                            print("      {}: {}".format(key, desc))
        
        print("\n" + "="*50)
    
    def extract_from_url(self):
        """Extract parameters from an existing Yad2 URL."""
        print("🔍 Extract Parameters from Yad2 URL")
        print("=" * 40)
        
        url = input("Enter the Yad2 URL: ").strip()
        
        if not url:
            print("❌ No URL provided.")
            return
        
        try:
            params_dict = URLUtils.extract_url_parameters(url)
            
            params = Yad2SearchParameters()
            extracted_count = 0
            
            for key, value in params_dict.items():
                try:
                    params.set_parameter(key, value)
                    extracted_count += 1
                except ValueError:
                    print("⚠️  Skipping unknown parameter: {}={}".format(key, value))
            
            print("\n✅ Extracted {} parameters:".format(extracted_count))
            print(params.to_json())
            print()
            
            return params
            
        except Exception as e:
            print("❌ Error parsing URL: {}".format(e))
            return None
    
    def main_menu(self):
        """Main menu for the interactive Yad2 search builder."""
        while True:
            print("\n🏠 Yad2 Search Builder - Main Menu")
            print("=" * 40)
            print("1. Quick Search (common parameters)")
            print("2. Advanced Search (all parameters)")
            print("3. Extract from existing URL")
            print("4. Parameter Reference Guide")
            print("5. Exit")
            print()
            
            choice = input("Choose an option (1-5): ").strip()
            
            if choice == '1':
                params = self.quick_search()
                if params:
                    self._offer_scraping(params)
            elif choice == '2':
                params = self.advanced_search()
                if params and params.get_active_parameters():
                    self._offer_scraping(params)
            elif choice == '3':
                params = self.extract_from_url()
                if params:
                    self._offer_scraping(params)
            elif choice == '4':
                self.show_parameter_reference()
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
    
    def _offer_scraping(self, params):
        """Offer to start scraping with the configured parameters."""
        print("\n🤖 Scraping Options")
        print("=" * 20)
        print("1. Just show the URL")
        print("2. Start scraping (1-3 pages)")
        print("3. Go back to main menu")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == '1':
            print("\n🔗 Your search URL:")
            print(params.build_url())
        elif choice == '2':
            try:
                max_pages = input("Number of pages to scrape (1-10, default 2): ").strip()
                max_pages = int(max_pages) if max_pages else 2
                max_pages = max(1, min(10, max_pages))  # Clamp between 1-10
                
                print("\n🚀 Starting scraper...")
                scraper = Yad2Scraper(params)
                assets = scraper.scrape_all_pages(max_pages=max_pages, delay=2)
                
                if assets:
                    print("\n✅ Scraping completed!")
                    print("Found {} assets".format(len(assets)))
                    
                    # Save option
                    save = input("\nSave results to file? (y/n): ").strip().lower()
                    if save in ['y', 'yes']:
                        filename = scraper.save_to_json()
                        print("Results saved to: {}".format(filename))
                else:
                    print("\n❌ No assets found.")
                
            except ValueError:
                print("❌ Invalid number of pages.")
            except KeyboardInterrupt:
                print("\n⏹️ Scraping cancelled.")
            except Exception as e:
                print("\n❌ Error during scraping: {}".format(e))


def main():
    """Main entry point for the CLI."""
    try:
        cli = InteractiveCLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print("\n❌ Unexpected error: {}".format(e))


if __name__ == "__main__":
    main() 