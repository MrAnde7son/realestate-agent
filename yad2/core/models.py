#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Data Models

Data classes and models for real estate assets and related entities.
"""

from datetime import datetime
from typing import Any, Dict


class RealEstateListing:
    """Data class for real estate assets."""
    
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.price = kwargs.get('price')
        self.previous_price = kwargs.get('previous_price')
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
        self.contact_name = kwargs.get('contact_name')
        self.contact_phone = kwargs.get('contact_phone')
        self._contact_info = None
        self.contact_info = kwargs.get('contact_info')
        self.features = kwargs.get('features', {})
        self.url = kwargs.get('url')
        self.listing_id = kwargs.get('listing_id')
        self.date_posted = kwargs.get('date_posted')
        self.coordinates = kwargs.get('coordinates')
        self.listing_type = kwargs.get('listing_type')
        self.ad_type = kwargs.get('ad_type')
        self.recent_deal = kwargs.get('recent_deal')
        self.scraped_at = datetime.now().isoformat()
        self.meta = {}

    @staticmethod
    def _coerce_contact_info(contact_info: Any) -> Dict[str, Any]:
        """Return a plain dictionary representation of contact information."""

        if contact_info is None:
            return {}
        if isinstance(contact_info, dict):
            return contact_info
        if hasattr(contact_info, "to_dict"):
            try:
                data = contact_info.to_dict()
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

        data = {
            'id': getattr(contact_info, 'id', None),
            'name': getattr(contact_info, 'name', None),
            'phone': getattr(contact_info, 'phone', None),
            'brokerPhone': getattr(contact_info, 'brokerPhone', None),
            'isVirtualPhoneNumber': getattr(contact_info, 'isVirtualPhoneNumber', None),
            'agencyName': getattr(contact_info, 'agencyName', None),
            'agencyLogo': getattr(contact_info, 'agencyLogo', None),
            'brokerAvatar': getattr(contact_info, 'brokerAvatar', None),
            'agencyAbout': getattr(contact_info, 'agencyAbout', None),
            'brokers': getattr(contact_info, 'brokers', None),
            'licenseNumber': getattr(contact_info, 'licenseNumber', None),
        }
        return {k: v for k, v in data.items() if v is not None}

    @property
    def contact_info(self) -> Any:
        return self._contact_info

    @contact_info.setter
    def contact_info(self, value: Any) -> None:
        self._contact_info = value
        if value is None:
            return
        contact_dict = self._coerce_contact_info(value)
        if getattr(self, "contact_name", None) is None:
            self.contact_name = contact_dict.get('name')
        if getattr(self, "contact_phone", None) is None:
            self.contact_phone = contact_dict.get('phone') or contact_dict.get('brokerPhone')
    
    def to_dict(self):
        """Convert to dictionary."""
        contact_info = self._coerce_contact_info(self.contact_info)
        contact_name = self.contact_name or contact_info.get('name')
        contact_phone = self.contact_phone or contact_info.get('phone') or contact_info.get('brokerPhone')

        images = getattr(self, "images", None)
        if images in (None, ""):
            images_list = []
        elif isinstance(images, (list, tuple, set)):
            images_list = [img for img in images if img]
        else:
            images_list = [images]

        video_value = getattr(self, "video", None)
        if isinstance(video_value, dict):
            video_value = video_value.get("url") or video_value.get("src")

        return {
            'title': self.title,
            'price': self.price,
            'previous_price': self.previous_price,
            'address': self.address,
            'rooms': self.rooms,
            'floor': self.floor,
            'size': self.size,
            'total_size': self.total_size,
            'property_type': self.property_type,
            'description': self.description,
            'images': images_list,
            'photos': images_list,
            'video': video_value,
            'documents': self.documents,
            'contact_info': contact_info or None,
            'contact_name': contact_name,
            'contact_phone': contact_phone,
            'features': self.features,
            'url': self.url,
            'listing_id': self.listing_id,
            'date_posted': self.date_posted,
            'coordinates': self.coordinates,
            'listing_type': self.listing_type,
            'ad_type': self.ad_type,
            'recent_deal': bool(self.recent_deal) if self.recent_deal is not None else False,
            'scraped_at': self.scraped_at,
            'meta': self.meta,
        }
    
    def __str__(self):
        """String representation."""
        return f"RealEstateListing({', '.join([f'{k}={v}' for k, v in self.to_dict().items() if v is not None])})"
    
    def __repr__(self):
        return self.__str__()



class Contact:
    def __init__(self, **kwargs):
        def _get(*keys):
            for key in keys:
                if key in kwargs and kwargs[key] is not None:
                    return kwargs[key]
            return None

        self.id: int = _get('id')
        self.name: str = _get('name')
        self.phone: str = _get('phone')
        self.brokerPhone: str = _get('broker_phone', 'brokerPhone')
        self.isVirtualPhoneNumber: bool = _get('is_virtual_phone_number', 'isVirtualPhoneNumber')
        self.agencyName: str = _get('agency_name', 'agencyName')
        self.agencyLogo: str = _get('agency_logo', 'agencyLogo')
        self.brokerAvatar: str = _get('broker_avatar', 'brokerAvatar')
        self.agencyAbout: str = _get('agency_about', 'agencyAbout')
        brokers = _get('brokers')
        self.brokers = brokers if brokers is not None else []
        self.licenseNumber = _get('license_number', 'licenseNumber')

    def to_dict(self):
        return {
            'id': self.id,
            'brokerPhone': self.brokerPhone,
            'name': self.name,
            'phone': self.phone,
            'isVirtualPhoneNumber': self.isVirtualPhoneNumber,
            'agencyName': self.agencyName,
            'agencyLogo': self.agencyLogo,
            'brokerAvatar': self.brokerAvatar,
            'agencyAbout': self.agencyAbout,
            'brokers': self.brokers,
            'licenseNumber': self.licenseNumber,
        }

    def __str__(self):
        return "Contact(name='{}', phone={})".format(
            self.name or 'N/A',
            self.phone or 'N/A'
        )

    def __repr__(self):
        return self.__str__()
