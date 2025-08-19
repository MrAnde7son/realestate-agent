#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gov.nadlan.models import Deal

# Test parsing parcel number
test_data = {
    'parcelNum': '6638-68-5',
    'address': 'הרוגי מלכות 14',
    'dealAmount': 5600000
}

deal = Deal.from_item(test_data)
print(f'Address: {deal.address}')
print(f'Parcel Gush: {deal.parcel_gush}')
print(f'Parcel Helka: {deal.parcel_helka}')
print(f'Parcel Sub-Helka: {deal.parcel_sub_helka}')
print(f'Raw parcelNum: {deal.raw.get("parcelNum")}')

# Test with different parcel number formats
test_cases = [
    '6638-68-5',    # Full format
    '1234-56',      # Missing sub-helka
    '789',          # Only gush
    '',             # Empty string
    None            # None value
]

print("\nTesting different parcel number formats:")
for parcel_num in test_cases:
    gush, helka, sub_helka = Deal._parse_parcel_num(parcel_num)
    print(f'"{parcel_num}" -> Gush: {gush}, Helka: {helka}, Sub-Helka: {sub_helka}')
