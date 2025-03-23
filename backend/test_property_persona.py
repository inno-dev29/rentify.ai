#!/usr/bin/env python
import os
import sys
import django
import json
import logging
import requests
import time
import re
from typing import Dict, Any

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models and services after Django setup
from properties.models import Property
from llm_services.services.llm_client import format_property_data, ClaudeClient
from django.conf import settings

# Claude API constants
CLAUDE_BASE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_KEY = settings.CLAUDE_API_KEY
CLAUDE_MODEL = "claude-3-sonnet-20240229"

def get_property_data(property_id: int) -> Dict[str, Any]:
    """Format property data for the prompt"""
    try:
        property_obj = Property.objects.get(id=property_id)
        
        # Get amenities for this property
        amenities = [amenity.name for amenity in property_obj.amenities.all()]
        
        # Convert decimal values to strings to make them JSON serializable
        return {
            "id": property_obj.id,
            "title": property_obj.title,
            "description": property_obj.description,
            "property_type": property_obj.property_type,
            "bedroom_count": property_obj.bedroom_count,
            "bathroom_count": str(property_obj.bathroom_count),
            "max_guests": property_obj.max_guests,
            "base_price": str(property_obj.base_price),
            "location": {
                "city": property_obj.city,
                "state": property_obj.state,
                "country": property_obj.country,
                "address_line1": property_obj.address_line1,
                "address_line2": property_obj.address_line2 if property_obj.address_line2 else ""
            },
            "amenities": amenities,
        }
    except Property.DoesNotExist:
        raise ValueError(f"Property with ID {property_id} not found")

def fix_json_format(content: str) -> str:
    """Apply comprehensive fixes to make JSON parseable"""
    # Step 1: Check if we need to add the opening brace
    if not content.startswith('{'):
        content = '{' + content
        logger.info("Added missing opening brace")
    
    # Step 2: Handle newlines and control characters
    # Replace all newlines, tabs, and multiple spaces with a single space in non-string contexts
    # This regex-based approach is safer than simple replacement
    
    # First, let's normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Make a multi-pass attempt at fixing the JSON
    
    # Attempt 1: Basic single-quote replacement and missing quotes around property names
    fixed_content = content.replace("'", '"')
    if not fixed_content.startswith('{"'):
        # Try to add quotes around property names
        # This is a very simplified approach and might not work for complex cases
        fixed_content = fixed_content.replace('{', '{"')
        fixed_content = fixed_content.replace(':', '":')
        fixed_content = fixed_content.replace(',', ',"')
        # Fix double quotes created by our replacements
        fixed_content = fixed_content.replace('""', '"')
    
    try:
        # Try to parse with basic fixes
        json.loads(fixed_content)
        logger.info("First pass JSON fixing succeeded")
        return fixed_content
    except json.JSONDecodeError:
        logger.info("First pass JSON fixing failed, trying more aggressive approaches")
    
    # Attempt 2: More aggressive cleaning
    # Start with our original content again
    try:
        # Approach: Build a valid JSON object from scratch using regex patterns to extract keys and values
        # This is a simplified approach for our specific format
        
        # Extract all clear key-value patterns we can find
        result_dict = {}
        
        # Extract the structure using regex for our specific format
        ideal_guests_match = re.search(r'"?ideal_guests"?\s*:\s*{([^}]+)}', content, re.DOTALL)
        if ideal_guests_match:
            ideal_section = ideal_guests_match.group(1)
            demographics_match = re.search(r'"?demographics"?\s*:\s*\[(.*?)\]', ideal_section, re.DOTALL)
            traveler_match = re.search(r'"?traveler_types"?\s*:\s*\[(.*?)\]', ideal_section, re.DOTALL)
            
            result_dict["ideal_guests"] = {
                "demographics": parse_string_array(demographics_match.group(1) if demographics_match else ""),
                "traveler_types": parse_string_array(traveler_match.group(1) if traveler_match else "")
            }
        
        use_cases_match = re.search(r'"?use_cases"?\s*:\s*{([^}]+)}', content, re.DOTALL)
        if use_cases_match:
            uses_section = use_cases_match.group(1)
            primary_match = re.search(r'"?primary"?\s*:\s*\[(.*?)\]', uses_section, re.DOTALL)
            secondary_match = re.search(r'"?secondary"?\s*:\s*\[(.*?)\]', uses_section, re.DOTALL)
            
            result_dict["use_cases"] = {
                "primary": parse_string_array(primary_match.group(1) if primary_match else ""),
                "secondary": parse_string_array(secondary_match.group(1) if secondary_match else "")
            }
        
        unique_attr_match = re.search(r'"?unique_attributes"?\s*:\s*{([^}]+)}', content, re.DOTALL)
        if unique_attr_match:
            unique_section = unique_attr_match.group(1)
            selling_points_match = re.search(r'"?key_selling_points"?\s*:\s*\[(.*?)\]', unique_section, re.DOTALL)
            amenities_match = re.search(r'"?stand_out_amenities"?\s*:\s*\[(.*?)\]', unique_section, re.DOTALL)
            
            result_dict["unique_attributes"] = {
                "key_selling_points": parse_string_array(selling_points_match.group(1) if selling_points_match else ""),
                "stand_out_amenities": parse_string_array(amenities_match.group(1) if amenities_match else "")
            }
        
        atmosphere_match = re.search(r'"?atmosphere"?\s*:\s*{([^}]+)}', content, re.DOTALL)
        if atmosphere_match:
            atmosphere_section = atmosphere_match.group(1)
            vibe_match = re.search(r'"?overall_vibe"?\s*:\s*"([^"]+)"', atmosphere_section)
            descriptors_match = re.search(r'"?descriptors"?\s*:\s*\[(.*?)\]', atmosphere_section, re.DOTALL)
            
            result_dict["atmosphere"] = {
                "overall_vibe": vibe_match.group(1) if vibe_match else "comfortable",
                "descriptors": parse_string_array(descriptors_match.group(1) if descriptors_match else "")
            }
        
        market_match = re.search(r'"?market_position"?\s*:\s*{([^}]+)}', content, re.DOTALL)
        if market_match:
            market_section = market_match.group(1)
            property_class_match = re.search(r'"?property_class"?\s*:\s*"([^"]+)"', market_section)
            comparable_match = re.search(r'"?comparable_to"?\s*:\s*\[(.*?)\]', market_section, re.DOTALL)
            
            result_dict["market_position"] = {
                "property_class": property_class_match.group(1) if property_class_match else "mid-range",
                "comparable_to": parse_string_array(comparable_match.group(1) if comparable_match else "")
            }
        
        # Convert our dictionary back to a properly formatted JSON string
        return json.dumps(result_dict)
        
    except Exception as e:
        logger.error(f"Aggressive JSON fixing failed: {str(e)}")
        # Return our best attempt so far
        return fixed_content

def parse_string_array(text: str) -> list:
    """Extract strings from a potential array text"""
    # Clean up the text
    text = text.strip()
    
    # Use regex to find all quoted strings
    items = re.findall(r'"([^"]*)"', text)
    
    # If we found items with quotes, return them
    if items:
        return items
    
    # Fallback: split by commas and clean each item
    return [item.strip().strip('"').strip("'") for item in text.split(",") if item.strip()]

def reconstruct_json_from_claude(content: str) -> dict:
    """
    Special function to reconstruct JSON from Claude's text output
    when standard JSON parsing fails
    """
    # Base structure for property persona
    result = {
        "ideal_guests": {
            "demographics": [],
            "traveler_types": []
        },
        "use_cases": {
            "primary": [],
            "secondary": []
        },
        "unique_attributes": {
            "key_selling_points": [],
            "stand_out_amenities": []
        },
        "atmosphere": {
            "overall_vibe": "comfortable",
            "descriptors": []
        },
        "market_position": {
            "property_class": "mid-range",
            "comparable_to": []
        }
    }
    
    # Extract demographics
    demographics_match = re.search(r'"?demographics"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if demographics_match:
        result["ideal_guests"]["demographics"] = parse_string_array(demographics_match.group(1))
    
    # Extract traveler types
    traveler_match = re.search(r'"?traveler_types"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if traveler_match:
        result["ideal_guests"]["traveler_types"] = parse_string_array(traveler_match.group(1))
    
    # Extract primary use cases
    primary_match = re.search(r'"?primary"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if primary_match:
        result["use_cases"]["primary"] = parse_string_array(primary_match.group(1))
    
    # Extract secondary use cases
    secondary_match = re.search(r'"?secondary"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if secondary_match:
        result["use_cases"]["secondary"] = parse_string_array(secondary_match.group(1))
    
    # Extract key selling points
    selling_points_match = re.search(r'"?key_selling_points"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if selling_points_match:
        result["unique_attributes"]["key_selling_points"] = parse_string_array(selling_points_match.group(1))
    
    # Extract stand-out amenities
    amenities_match = re.search(r'"?stand_out_amenities"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if amenities_match:
        result["unique_attributes"]["stand_out_amenities"] = parse_string_array(amenities_match.group(1))
    
    # Extract overall vibe
    vibe_match = re.search(r'"?overall_vibe"?\s*:\s*"([^"]+)"', content)
    if vibe_match:
        result["atmosphere"]["overall_vibe"] = vibe_match.group(1)
    
    # Extract descriptors
    descriptors_match = re.search(r'"?descriptors"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if descriptors_match:
        result["atmosphere"]["descriptors"] = parse_string_array(descriptors_match.group(1))
    
    # Extract property class
    property_class_match = re.search(r'"?property_class"?\s*:\s*"([^"]+)"', content)
    if property_class_match:
        result["market_position"]["property_class"] = property_class_match.group(1)
    
    # Extract comparable properties
    comparable_match = re.search(r'"?comparable_to"?\s*:\s*\[(.*?)\]', content, re.DOTALL)
    if comparable_match:
        result["market_position"]["comparable_to"] = parse_string_array(comparable_match.group(1))
    
    return result

def test_claude_direct():
    """Test direct communication with Claude API for JSON responses"""
    property_id = 8  # Use a property that exists in your database
    logger.info(f"Starting test with property ID: {property_id}")
    
    try:
        # Format property data
        property_data = get_property_data(property_id)
        data_str = json.dumps(property_data, indent=2)
        logger.info(f"Property data formatted successfully ({len(data_str)} characters)")
        
        # System prompt with instructions for Claude
        system_prompt = """
        You are an expert in real estate market analysis for a rental platform. Your task is to generate 
        a comprehensive persona for a property based on its characteristics, amenities, and location.
        
        Create a detailed property persona that includes:
        1. Ideal guest types (demographic profiles that would enjoy this property most)
        2. Primary use cases (vacation, business travel, family gatherings, etc.)
        3. Unique selling points (what makes this property special)
        4. Atmosphere/vibe (the feeling guests would experience)
        5. Comparable properties (what category of accommodations this competes with)
        
        Return your response as a valid JSON object with the following structure:
        {
            "ideal_guests": {
                "demographics": ["Young professionals", "Retired couples", etc.],
                "traveler_types": ["Business travelers", "Vacationing families", etc.]
            },
            "use_cases": {
                "primary": ["Weekend getaways", "Business trips", etc.],
                "secondary": ["Remote work retreats", "Family reunions", etc.]
            },
            "unique_attributes": {
                "key_selling_points": ["Breathtaking ocean view", "Historic architecture", etc.],
                "stand_out_amenities": ["Infinity pool", "Chef's kitchen", etc.]
            },
            "atmosphere": {
                "overall_vibe": "cozy and rustic" or "sleek and modern" or "luxurious and exclusive",
                "descriptors": ["Peaceful", "Energetic", "Elegant", etc.]
            },
            "market_position": {
                "property_class": "budget" or "mid-range" or "luxury",
                "comparable_to": ["Boutique hotels", "Resort condos", etc.]
            }
        }
        
        Make sure to use proper JSON format with double quotes for all property names and string values.
        Do not include any explanation text outside of the JSON object.
        """
        
        # User prompt with property data
        user_prompt = f"""
        Please generate a comprehensive property persona based on the following property data:
        
        {data_str}
        """
        
        # Prepare headers for Claude API
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Attempt 1: Standard Claude messages without prefill
        payload1 = {
            "model": CLAUDE_MODEL,
            "system": system_prompt,
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        
        logger.info(f"Testing JSON extraction approach")
        logger.info(f"API key (masked): {CLAUDE_API_KEY[:4]}...{CLAUDE_API_KEY[-4:]}")
        
        # Make the API request
        response = requests.post(
            CLAUDE_BASE_URL,
            headers=headers,
            json=payload1,
            timeout=60
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Get the content from the response
            content = result["content"][0]["text"]
            
            # Log the entire raw response for inspection
            logger.info(f"Raw content (first 500 chars):\n{content[:500]}")
            logger.info(f"Raw content (last 100 chars):\n{content[-100:]}")
            
            # Try parsing as JSON directly first
            try:
                parsed_json = json.loads(content)
                logger.info("Successfully parsed as JSON directly!")
                logger.info(f"Keys: {list(parsed_json.keys())}")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"Initial JSON parsing error: {str(e)}")
                
                # Try fixing the JSON
                logger.info("Trying to fix JSON format...")
                fixed_content = fix_json_format(content)
                logger.info(f"Fixed content (first 100 chars): {fixed_content[:100]}...")
                
                try:
                    parsed_json = json.loads(fixed_content)
                    logger.info("Successfully parsed fixed JSON!")
                    logger.info(f"Keys: {list(parsed_json.keys())}")
                    return parsed_json
                except json.JSONDecodeError as e:
                    logger.error(f"Still couldn't parse fixed JSON: {str(e)}")
                    
                    # Last resort: extract JSON structure with regex
                    logger.info("Using regex-based JSON extraction as last resort")
                    extracted_json = reconstruct_json_from_claude(content)
                    logger.info(f"Successfully extracted JSON structure with {len(extracted_json)} top-level keys")
                    logger.info(f"Extracted keys: {list(extracted_json.keys())}")
                    return extracted_json
        else:
            logger.error(f"API error ({response.status_code}): {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_claude_direct()
    if result:
        print("\nFinal persona result:")
        print(f"Ideal guests: {result['ideal_guests']['demographics']}")
        print(f"Primary use cases: {result['use_cases']['primary']}")
        print(f"Key selling points: {result['unique_attributes']['key_selling_points']}")
        print(f"Overall vibe: {result['atmosphere']['overall_vibe']}")
        print(f"Property class: {result['market_position']['property_class']}") 