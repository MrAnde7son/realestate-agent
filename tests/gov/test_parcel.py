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
print(f'Parcel block: {deal.parcel_block}')
print(f'Parcel parcel: {deal.parcel_parcel}')
print(f'Parcel Sub-parcel: {deal.parcel_sub_parcel}')
print(f'Raw parcelNum: {deal.raw.get("parcelNum")}')

# Test with different parcel number formats
test_cases = [
    '6638-68-5',    # Full format
    '1234-56',      # Missing sub-parcel
    '789',          # Only block
    '',             # Empty string
    None            # None value
]

print("\nTesting different parcel number formats:")
for parcel_num in test_cases:
    block, parcel, sub_parcel = Deal._parse_parcel_num(parcel_num)
    print(f'"{parcel_num}" -> block: {block}, parcel: {parcel}, Sub-parcel: {sub_parcel}')
