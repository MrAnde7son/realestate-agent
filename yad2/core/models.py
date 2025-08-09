#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Data Models

Data classes and models for real estate listings and related entities.
"""

from datetime import datetime


class RealEstateListing:
    """Data class for real estate listings."""
    
    def __init__(self):
        self.title = None
        self.price = None
        self.address = None
        self.rooms = None
        self.floor = None
        self.size = None
        self.property_type = None
        self.description = None
        self.images = []
        self.contact_info = None
        self.features = {}
        self.url = None
        self.listing_id = None
        self.date_posted = None
        self.coordinates = None
        self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'address': self.address,
            'rooms': self.rooms,
            'floor': self.floor,
            'size': self.size,
            'property_type': self.property_type,
            'description': self.description,
            'images': self.images,
            'contact_info': self.contact_info,
            'features': self.features,
            'url': self.url,
            'listing_id': self.listing_id,
            'date_posted': self.date_posted,
            'coordinates': self.coordinates,
            'scraped_at': self.scraped_at
        }
    
    def __str__(self):
        """String representation."""
        return "RealEstateListing(title='{}', price={}, address='{}')".format(
            self.title or 'N/A', 
            self.price or 'N/A', 
            self.address or 'N/A'
        )
    
    def __repr__(self):
        return self.__str__() 