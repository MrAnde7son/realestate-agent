#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Data Models

Data classes and models for real estate assets and related entities.
"""

from datetime import datetime


class RealEstateListing:
    """Data class for real estate assets."""
    
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.price = kwargs.get('price')
        self.address = kwargs.get('address')
        self.rooms = kwargs.get('rooms')
        self.floor = kwargs.get('floor')
        self.size = kwargs.get('size')
        self.total_size = kwargs.get('total_size')
        self.property_type = kwargs.get('property_type')
        self.description = kwargs.get('description')
        self.images = kwargs.get('images', [])
        self.video = kwargs.get('video')
        self.documents = kwargs.get('documents', [])
        self.contact_info = kwargs.get('contact_info')
        self.features = kwargs.get('features', {})
        self.url = kwargs.get('url')
        self.listing_id = kwargs.get('listing_id')
        self.date_posted = kwargs.get('date_posted')
        self.coordinates = kwargs.get('coordinates')
        self.scraped_at = datetime.now().isoformat()
        self.meta = {}
    
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
            'video': self.video,
            'documents': self.documents,
            'contact_info': self.contact_info,
            'features': self.features,
            'url': self.url,
            'listing_id': self.listing_id,
            'date_posted': self.date_posted,
            'coordinates': self.coordinates,
            'scraped_at': self.scraped_at,
            'meta': self.meta,
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


class Contact:
    def __init__(self, **kwargs):
        self.brokerPhone: str = kwargs.get('broker_phone')
        self.id: int = kwargs.get('id')
        self.name: str = kwargs.get('name')
        self.name: str = kwargs.get('name')
        self.phone: str = kwargs.get('phone')

    def to_dict(self):
        return {
            'brokerPhone': self.brokerPhone,
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
        }

    def __str__(self):
        return "Contact(name='{}', phome={})".format(
            self.name or 'N/A',
            self.phone or 'N/A'
        )

    def __repr__(self):
        return self.__str__()