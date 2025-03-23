#!/usr/bin/env python
"""
This script adds sample images to properties in the database.
Run with: python add_property_images.py
"""

import os
import sys
import django
import tempfile
from PIL import Image, ImageDraw, ImageFont
from django.core.files.images import ImageFile
from django.utils.text import slugify

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from properties.models import Property, PropertyImage

def create_placeholder_image(width, height, color, text):
    """Create a placeholder image with text."""
    image = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(image)
    
    # Draw rectangle border
    draw.rectangle(
        [(10, 10), (width-10, height-10)],
        outline='white',
        width=2
    )
    
    # Add text
    text_width, text_height = draw.textsize(text) if hasattr(draw, 'textsize') else (width//2, height//4)
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(
        position,
        text,
        fill='white'
    )
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    image.save(temp_file.name, format='JPEG')
    
    # Return a file that Django can use
    return temp_file.name

def add_property_images():
    """Add sample images to properties."""
    print("Adding sample images to properties...")
    
    # Get all properties
    properties = Property.objects.all()
    
    if not properties:
        print("No properties found in the database.")
        return
    
    for prop in properties:
        print(f"\nProcessing property: {prop.id} - {prop.title}")
        
        # Skip if property already has images
        if prop.images.exists():
            print(f"Property {prop.id} already has {prop.images.count()} images. Skipping.")
            continue
        
        # Determine colors based on property title
        title_lower = prop.title.lower()
        colors = ['#3498db', '#2ecc71', '#e74c3c']  # Blue, Green, Red
        
        # Adjust colors based on property type
        if 'beach' in title_lower or 'ocean' in title_lower:
            colors = ['#1abc9c', '#3498db', '#2980b9']  # Teal, Blue, Dark Blue
        elif 'mountain' in title_lower or 'cabin' in title_lower:
            colors = ['#27ae60', '#2ecc71', '#8e44ad']  # Green, Light Green, Purple
        elif 'city' in title_lower or 'apartment' in title_lower:
            colors = ['#2c3e50', '#7f8c8d', '#95a5a6']  # Dark Blue, Gray, Light Gray
        
        # Create 3 images for each property
        for i, color in enumerate(colors):
            print(f"  Creating image {i+1} with color {color} for property {prop.id}")
            
            # Create placeholder image
            text = f"{prop.title} - Image {i+1}"
            image_path = create_placeholder_image(800, 600, color, text)
            
            # Create unique filename
            filename = f"{slugify(prop.title)}-{i+1}.jpg"
            
            try:
                # Create and save the property image instance
                image = PropertyImage(
                    property=prop,
                    caption=f"Sample image {i+1} for {prop.title}",
                    is_primary=(i == 0)  # First image is primary
                )
                
                # Open the image file and save it
                with open(image_path, 'rb') as f:
                    image.image.save(filename, ImageFile(f), save=True)
                
                print(f"  Added image {i+1} to property {prop.id}")
                
                # Clean up the temporary file
                os.unlink(image_path)
            except Exception as e:
                print(f"  Error adding image {i+1} to property {prop.id}: {e}")
                if os.path.exists(image_path):
                    os.unlink(image_path)
    
    # Print summary
    total_images = PropertyImage.objects.count()
    print(f"\nAdded images successfully. Total images in database: {total_images}")

if __name__ == "__main__":
    add_property_images() 