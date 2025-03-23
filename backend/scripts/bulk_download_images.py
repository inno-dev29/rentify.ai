#!/usr/bin/env python
"""
This script facilitates bulk downloading of images for multiple properties using a JSON file.
Run with: python scripts/bulk_download_images.py --file=images.json

The JSON file should have the following format:
[
    {
        "property_id": 1, 
        "images": [
            {
                "url": "https://example.com/image1.jpg",
                "caption": "Beautiful living room",
                "is_primary": true
            },
            {
                "url": "https://example.com/image2.jpg",
                "caption": "Master bedroom" 
            }
        ]
    },
    {
        "property_id": 2,
        "images": [
            {"url": "https://example.com/property2-image1.jpg"}
        ]
    }
]
"""

import os
import sys
import json
import django
import argparse

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom script for downloading images
from scripts.download_property_images import add_image_to_property

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

def process_json_file(file_path):
    """Process a JSON file with property image information."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: JSON file should contain a list of property objects.")
            return
        
        total_properties = len(data)
        total_images = sum(len(property_data.get('images', [])) for property_data in data)
        
        print(f"Found {total_properties} properties with a total of {total_images} images to process.")
        
        successful_properties = 0
        successful_images = 0
        
        for property_data in data:
            property_id = property_data.get('property_id')
            if not property_id:
                print("Warning: Property entry missing property_id, skipping.")
                continue
            
            images = property_data.get('images', [])
            if not images:
                print(f"Warning: No images found for property ID {property_id}, skipping.")
                continue
            
            property_success = 0
            for i, image_data in enumerate(images):
                url = image_data.get('url')
                if not url:
                    print(f"Warning: Image entry for property ID {property_id} missing URL, skipping.")
                    continue
                
                caption = image_data.get('caption')
                is_primary = image_data.get('is_primary', False)
                
                # Only apply primary to the first image if multiple are marked primary
                if is_primary and any(img.get('is_primary', False) for img in images[:i]):
                    print(f"Warning: Multiple images marked as primary for property ID {property_id}. Using only the first.")
                    is_primary = False
                
                if add_image_to_property(property_id, url, is_primary, caption):
                    property_success += 1
                    successful_images += 1
            
            if property_success > 0:
                successful_properties += 1
                print(f"Successfully added {property_success}/{len(images)} images to property ID {property_id}.")
            else:
                print(f"Failed to add any images to property ID {property_id}.")
        
        print(f"\nSummary:")
        print(f"- Processed {total_properties} properties")
        print(f"- {successful_properties} properties received at least one image")
        print(f"- {successful_images}/{total_images} images were successfully added")
    
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not valid JSON.")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"Unexpected error processing file: {e}")

def main():
    """Main function to parse arguments and process file."""
    parser = argparse.ArgumentParser(description='Bulk download images for properties from a JSON file.')
    parser.add_argument('--file', required=True, help='Path to the JSON file with property image information')
    
    args = parser.parse_args()
    process_json_file(args.file)

if __name__ == "__main__":
    main() 