#!/usr/bin/env python
"""
This script fixes the property summary generation in llm_client.py by ensuring Decimal objects
are correctly converted to float or string values for JSON serialization.
"""

import os
import sys
import re
import json
from decimal import Decimal

def fix_file():
    """Fixes the llm_client.py file."""
    filepath = 'llm_services/services/llm_client.py'
    
    print(f"Reading {filepath}...")
    
    # Read the current content
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Look for the format_property_data function
    format_func_pattern = r'def format_property_data\([^)]*\)[\s\S]*?review_data\.append\({[\s\S]*?}\)'
    format_func_match = re.search(format_func_pattern, content)
    
    if format_func_match:
        original_section = format_func_match.group(0)
        new_section = original_section.replace(
            'review_data.append({',
            'review_data.append({\n            "rating": float(review.rating),'
        )
        new_section = new_section.replace('"rating": review.rating,', '"rating": float(review.rating),')
        content = content.replace(original_section, new_section)
        print("Updated review ratings to convert to float.")
    
    # Fix the property data dictionary to convert Decimal fields to strings
    property_dict_pattern = r'"bathroom_count": property_obj\.bathroom_count,'
    content = content.replace(
        property_dict_pattern, 
        '"bathroom_count": str(property_obj.bathroom_count),'
    )
    print("Updated bathroom_count to convert to string.")
    
    property_dict_pattern = r'"base_price": property_obj\.base_price,'
    content = content.replace(
        property_dict_pattern, 
        '"base_price": str(property_obj.base_price),'
    )
    print("Updated base_price to convert to string.")
    
    # Fix the average_rating calculation
    avg_rating_pattern = r'"average_rating": sum\(r\["rating"\] for r in review_data\) / len\(review_data\) if review_data else None'
    content = content.replace(
        avg_rating_pattern, 
        '"average_rating": float(sum(r["rating"] for r in review_data) / len(review_data)) if review_data else None'
    )
    print("Updated average_rating to convert to float.")
    
    # Fix property address
    address_pattern = r'"address": property_obj\.address'
    if address_pattern in content:
        content = content.replace(
            address_pattern,
            '"address_line1": property_obj.address_line1,\n            "address_line2": property_obj.address_line2 if property_obj.address_line2 else ""'
        )
        print("Updated address to use address_line1 and address_line2.")
    
    # Write the updated content
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Updated {filepath} successfully.")
    
if __name__ == "__main__":
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
    
    import django
    django.setup()
    
    # Fix the file
    fix_file()
    
    # Test if the fix worked
    print("\nTesting if the fix worked...")
    from properties.models import Property
    from llm_services.services.llm_client import generate_property_summary
    
    property_obj = Property.objects.first()
    if property_obj:
        try:
            result = generate_property_summary(property_obj)
            print(f"✅ Property summary generated successfully!")
            print(f"Summary: {result['summary'][:100]}...")
            print(f"Highlights: {result['highlights']}")
        except Exception as e:
            print(f"❌ Error generating property summary: {str(e)}")
    else:
        print("❌ No properties found in the database.") 