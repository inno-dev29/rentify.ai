#!/usr/bin/env python
"""
This script lists all properties and their current images.
Run with: python scripts/list_properties.py

Options:
--no-images: Show only properties with no images
--id: Filter properties by ID
--type: Filter properties by type (house, apartment, etc.)
--output-json: Output the results as a JSON file that can be used with bulk_download_images.py
"""

import os
import sys
import json
import django
import argparse

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from properties.models import Property, PropertyImage

def list_properties(no_images=False, property_id=None, property_type=None, output_json=None):
    """List properties and their images."""
    # Build the query
    query = Property.objects.all()
    
    if property_id:
        query = query.filter(id=property_id)
    
    if property_type:
        query = query.filter(property_type=property_type)
    
    # Get the properties
    properties = query.order_by('id')
    
    if not properties:
        print("No properties found matching the criteria.")
        return
    
    # Prepare data structure for output
    property_data = []
    
    for prop in properties:
        images = prop.images.all()
        
        # Skip properties with images if --no-images flag is set
        if no_images and images.exists():
            continue
        
        print(f"\nProperty ID: {prop.id}")
        print(f"Title: {prop.title}")
        print(f"Type: {prop.property_type}")
        print(f"Location: {prop.city}, {prop.state}, {prop.country}")
        
        if images.exists():
            print(f"Images ({images.count()}):")
            for i, img in enumerate(images, 1):
                primary_str = " (Primary)" if img.is_primary else ""
                print(f"  {i}. {img.image.url}{primary_str}")
                if img.caption:
                    print(f"     Caption: {img.caption}")
        else:
            print("Images: None")
        
        # Collect data for JSON output
        if output_json:
            prop_entry = {
                "property_id": prop.id,
                "images": []
            }
            
            # Include existing images in the JSON output
            for img in images:
                img_entry = {
                    "url": img.image.url,
                    "caption": img.caption,
                    "is_primary": img.is_primary
                }
                prop_entry["images"].append(img_entry)
            
            property_data.append(prop_entry)
    
    # Write JSON file if requested
    if output_json and property_data:
        try:
            with open(output_json, 'w') as f:
                json.dump(property_data, f, indent=4)
            print(f"\nJSON data written to {output_json}")
        except Exception as e:
            print(f"\nError writing JSON file: {e}")

def main():
    """Main function to parse arguments and list properties."""
    parser = argparse.ArgumentParser(description='List properties and their images.')
    parser.add_argument('--no-images', action='store_true', help='Show only properties with no images')
    parser.add_argument('--id', type=int, help='Filter properties by ID')
    parser.add_argument('--type', choices=['house', 'apartment', 'condo', 'townhouse', 'villa', 'cabin', 'other'], 
                        help='Filter properties by type')
    parser.add_argument('--output-json', help='Output the results as a JSON file')
    
    args = parser.parse_args()
    
    list_properties(args.no_images, args.id, args.type, args.output_json)

if __name__ == "__main__":
    main() 