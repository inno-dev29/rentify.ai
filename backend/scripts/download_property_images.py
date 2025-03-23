#!/usr/bin/env python
"""
This script downloads images from URLs and adds them to properties in the database.
Run with: python scripts/download_property_images.py

Usage examples:
- Add a single image to a property:
  python scripts/download_property_images.py --property-id=1 --url="https://example.com/image.jpg"

- Add multiple images to a property:
  python scripts/download_property_images.py --property-id=1 --url="https://example.com/image1.jpg" --url="https://example.com/image2.jpg"

- Make the first image primary:
  python scripts/download_property_images.py --property-id=1 --url="https://example.com/image.jpg" --primary
"""

import os
import sys
import django
import argparse
import requests
import tempfile
from urllib.parse import urlparse
from django.core.files.images import ImageFile
from django.utils.text import slugify

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from properties.models import Property, PropertyImage

def download_image(url):
    """Download an image from a URL and save it to a temporary file."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Get the file extension from the URL or default to .jpg
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        _, ext = os.path.splitext(file_name)
        if not ext:
            ext = '.jpg'
        
        # Create a temporary file with the correct extension
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        
        # Write the image data to the file
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)
        
        temp_file.close()
        return temp_file.name, file_name
    
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None, None

def add_image_to_property(property_id, image_url, make_primary=False, caption=None):
    """Add an image from a URL to a property."""
    try:
        # Get the property
        try:
            property_obj = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            print(f"Property with ID {property_id} not found.")
            return False
        
        # Download the image
        image_path, original_filename = download_image(image_url)
        if not image_path:
            return False
        
        # Create a filename for the image
        if not caption:
            caption = f"Image for {property_obj.title}"
        
        filename = f"{slugify(property_obj.title)}-{original_filename}"
        
        # Determine if this should be primary
        is_primary = make_primary
        
        # If no images exist for this property and no primary flag, make it primary by default
        if not property_obj.images.exists() and not make_primary:
            is_primary = True
            print(f"No images exist for property {property_id}, making this the primary image.")
        
        try:
            # Create and save the property image instance
            image = PropertyImage(
                property=property_obj,
                caption=caption,
                is_primary=is_primary
            )
            
            # Open the image file and save it
            with open(image_path, 'rb') as f:
                image.image.save(filename, ImageFile(f), save=True)
            
            print(f"Added image to property {property_id} from {image_url}")
            
            # Clean up the temporary file
            os.unlink(image_path)
            return True
            
        except Exception as e:
            print(f"Error adding image to property {property_id}: {e}")
            if os.path.exists(image_path):
                os.unlink(image_path)
            return False
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Main function to parse arguments and add images."""
    parser = argparse.ArgumentParser(description='Download images from URLs and add them to properties.')
    parser.add_argument('--property-id', type=int, required=True, help='ID of the property to add images to')
    parser.add_argument('--url', action='append', required=True, help='URL(s) of the image(s) to download. Can be specified multiple times.')
    parser.add_argument('--primary', action='store_true', help='Make the first image the primary image')
    parser.add_argument('--caption', help='Caption for the image(s)')
    
    args = parser.parse_args()
    
    print(f"Adding {len(args.url)} image(s) to property ID {args.property_id}...")
    
    success_count = 0
    for i, url in enumerate(args.url):
        # Only apply primary to the first image if the flag is set
        make_primary = args.primary and i == 0
        
        if add_image_to_property(args.property_id, url, make_primary, args.caption):
            success_count += 1
    
    print(f"Successfully added {success_count}/{len(args.url)} images to property ID {args.property_id}.")

if __name__ == "__main__":
    main() 