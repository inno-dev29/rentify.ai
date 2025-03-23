"""
LLM client integration for the rental platform.
Supports multiple LLM providers (DeepSeek and Claude) with a unified interface.
"""

import json
import logging
import os
import requests
import time
import re
from typing import Dict, List, Optional, Union, Any
from django.conf import settings
from properties.models import Property
from users.models import User
from reviews.models import Review
from .cache import llm_cache

# Setup logging
logger = logging.getLogger(__name__)

class BaseLLMClient:
    """
    Base class for LLM clients with common functionality.
    Provides shared caching, debug mode, and mock response capabilities.
    """
    
    def __init__(self, debug_mode=None):
        """
        Initialize the base LLM client.
        
        Args:
            debug_mode: Override debug mode (default: read from settings.DEBUG_LLM)
        """
        # Set debug mode - can be overridden in initialization or read from settings
        self.debug_mode = debug_mode if debug_mode is not None else getattr(settings, 'DEBUG_LLM', False)
        if self.debug_mode:
            logger.info("LLM client initialized in DEBUG mode - no actual API calls will be made")
    
    def _get_mock_response(self, system_prompt, user_prompt, model, structured_output=None) -> Dict:
        """
        Generate a mock response when in debug mode.
        
        Args:
            system_prompt: Instructions for the LLM on how to respond
            user_prompt: The content to respond to
            model: LLM model being mocked
            structured_output: JSON schema for structured output (optional)
            
        Returns:
            Mock response dictionary
        """
        # Create a deterministic but unique mock response based on input
        import hashlib
        hash_input = f"{system_prompt}:{user_prompt}:{model}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        
        logger.info(f"Generating mock response with hash: {hash_value}")
        
        if structured_output:
            # Generate a valid response according to the schema
            try:
                # Simple example for common schemas
                if structured_output.get("properties", {}).get("summary"):
                    mock_content = json.dumps({
                        "summary": f"Mock property summary for debug mode. Hash: {hash_value}",
                        "highlights": [
                            "Debug highlight 1",
                            "Debug highlight 2",
                            "Debug highlight 3"
                        ]
                    })
                elif structured_output.get("properties", {}).get("persona"):
                    mock_content = json.dumps({
                        "persona": f"Mock persona for debug mode. Hash: {hash_value}",
                        "traits": ["Friendly", "Organized", "Professional"],
                        "preferences": ["Modern homes", "Urban locations", "Pet-friendly"]
                    })
                elif structured_output.get("properties", {}).get("recommendations"):
                    mock_content = json.dumps({
                        "recommendations": [
                            {"id": 1, "reason": "Mock recommendation 1"},
                            {"id": 2, "reason": "Mock recommendation 2"},
                            {"id": 3, "reason": "Mock recommendation 3"}
                        ]
                    })
                else:
                    # Generic mock response
                    mock_properties = {name: "Mock value" for name in structured_output.get("properties", {}).keys()}
                    mock_content = json.dumps(mock_properties)
            except Exception as e:
                logger.warning(f"Error creating structured mock response: {str(e)}")
                mock_content = json.dumps({"error": "Failed to create structured mock response"})
        else:
            # Plain text response
            mock_content = f"This is a mock response from the LLM client in debug mode.\nNo actual API call was made.\nResponse ID: {hash_value}"
        
        return {
            "content": mock_content,
            "model": model,
            "usage": {"input_tokens": 100, "output_tokens": 150},
            "stop_reason": "end_turn",
            "is_mock": True
        }
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        structured_output: Dict = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Send a prompt to the LLM and get a response.
        This method should be overridden by specific LLM client implementations.
        
        Args:
            system_prompt: Instructions for the LLM on how to respond
            user_prompt: The content to respond to
            model: Model to use
            max_tokens: Maximum response length
            temperature: Randomness parameter (0-1)
            structured_output: JSON schema for structured output (optional)
            use_cache: Whether to use the cache (default True)
            
        Returns:
            Dict containing the response text and metadata
        """
        raise NotImplementedError("This method must be implemented by subclasses")


class DeepSeekClient(BaseLLMClient):
    """
    Client for interacting with DeepSeek LLM API.
    Handles API requests, error handling, and response parsing.
    """
    
    BASE_URL = "https://api.deepseek.com/v1/chat/completions"
    DEFAULT_MODEL = "deepseek-chat"  # Replace with the correct model name
    
    def __init__(self, debug_mode=None):
        """
        Initialize the DeepSeek client with API key from settings.
        
        Args:
            debug_mode: Override debug mode (default: read from settings.DEBUG_LLM)
        """
        super().__init__(debug_mode)
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not self.api_key and not self.debug_mode:
            raise ValueError("DEEPSEEK_API_KEY not found in settings.")
            
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        structured_output: Dict = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Send a prompt to DeepSeek and get a response.
        
        Args:
            system_prompt: Instructions for the LLM on how to respond
            user_prompt: The content to respond to
            model: DeepSeek model to use (default is deepseek-chat)
            max_tokens: Maximum response length
            temperature: Randomness parameter (0-1)
            structured_output: JSON schema for structured output (optional)
            use_cache: Whether to use the cache (default True)
            
        Returns:
            Dict containing the response text and metadata
        """
        model = model or self.DEFAULT_MODEL
        
        # Check if we're in debug mode
        if self.debug_mode:
            logger.info("Using debug mode - returning mock response")
            return self._get_mock_response(system_prompt, user_prompt, model, structured_output)
        
        # Check cache first if enabled
        if use_cache and temperature < 0.2:  # Only cache deterministic responses
            cached_response = llm_cache.get(system_prompt, user_prompt, model)
            if cached_response:
                logger.info("Using cached LLM response")
                return cached_response
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add response format for structured output
        if structured_output:
            payload["response_format"] = {"type": "json_object"}
        
        # Retry mechanism
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Create response dict
                response_data = {
                    "content": result["choices"][0]["message"]["content"],
                    "model": result.get("model", model),
                    "usage": result.get("usage", {}),
                    "stop_reason": result["choices"][0].get("finish_reason", None)
                }
                
                # Cache the response if caching is enabled and the temperature is low enough
                if use_cache and temperature < 0.2:
                    llm_cache.set(system_prompt, user_prompt, model, response_data)
                
                return response_data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        # This should never be reached due to the raise in the loop
        raise RuntimeError("Failed to get response from DeepSeek API after multiple attempts")


class ClaudeClient(BaseLLMClient):
    """
    Client for interacting with the Claude API.
    Handles API requests, error handling, and response parsing.
    """
    
    BASE_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-3-sonnet-20240229"
    
    def __init__(self, debug_mode=None):
        """
        Initialize the Claude client with the API key.
        
        Args:
            debug_mode: Override debug mode (default: read from settings.DEBUG_LLM)
        """
        super().__init__(debug_mode)
        self.api_key = getattr(settings, 'CLAUDE_API_KEY', '')
        if not self.api_key and not self.debug_mode:
            raise ValueError("CLAUDE_API_KEY not found in settings or environment variables")
            
        # Log API key validation (first 4 chars and last 4 chars without revealing full key)
        if self.api_key and len(self.api_key) > 8:
            logger.info(f"Claude API key found: {self.api_key[:4]}...{self.api_key[-4:]}")
        else:
            logger.warning("Claude API key is missing or too short")
        
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Verify the API key format
        if self.api_key and not self.debug_mode:
            if not self.api_key.startswith("sk-ant-"):
                logger.warning("Claude API key doesn't have the expected format (should start with 'sk-ant-')")
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        structured_output: Dict = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Send a prompt to Claude and get a response.
        
        Args:
            system_prompt: Instructions for Claude on how to respond
            user_prompt: The content to respond to
            model: Claude model to use (default is claude-3-sonnet)
            max_tokens: Maximum response length
            temperature: Randomness parameter (0-1)
            structured_output: JSON schema for structured output (optional)
            use_cache: Whether to use the cache (default True)
            
        Returns:
            Dict containing the response text and metadata
        """
        model = model or self.DEFAULT_MODEL
        
        # Check if we're in debug mode
        if self.debug_mode:
            logger.info("Using debug mode - returning mock response")
            return self._get_mock_response(system_prompt, user_prompt, model, structured_output)
        
        # Check cache first if enabled
        if use_cache and temperature < 0.2:  # Only cache deterministic responses
            cached_response = llm_cache.get(system_prompt, user_prompt, model)
            if cached_response:
                logger.info("Using cached LLM response")
                return cached_response
        
        # Ensure user_prompt is a string
        if not isinstance(user_prompt, str):
            user_prompt = str(user_prompt)
            
        # Construct payload
        payload = {
            "model": model,
            "system": system_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Prepare messages array
        messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        # Handle structured output for JSON
        if structured_output:
            # Update system prompt to explicitly request JSON format
            if "Return your response as a valid JSON" not in payload["system"]:
                payload["system"] += "\nMake sure to return your response as a valid JSON object."
                logger.debug(f"Updated system prompt for JSON: {payload['system']}")
            
            # Use prefilled response technique for Claude JSON responses
            messages.append({"role": "assistant", "content": "{\n  \""})
            logger.debug("Added prefilled response for JSON output")
        
        # Add messages to payload
        payload["messages"] = messages
        
        # Log the request for debugging
        logger.info(f"Sending Claude API request with model: {model}")
        logger.debug(f"Claude API payload: {json.dumps(payload, indent=2)}")
        
        # Retry mechanism
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Log the attempt
                logger.info(f"Claude API request attempt {attempt+1}/{max_retries}")
                
                response = requests.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                # For debugging: log the response status and headers
                logger.debug(f"Claude API response status: {response.status_code}")
                logger.debug(f"Claude API response headers: {response.headers}")
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Claude API error ({response.status_code}): {error_detail}")
                    
                    # More detailed error handling based on status code
                    if response.status_code == 401:
                        raise requests.exceptions.HTTPError(f"Claude API authentication error (401): Invalid API key or authentication failure")
                    elif response.status_code == 400:
                        try:
                            error_json = response.json()
                            error_message = error_json.get("error", {}).get("message", "Unknown error")
                            error_type = error_json.get("error", {}).get("type", "Unknown error type")
                            logger.error(f"Claude API error type: {error_type}, message: {error_message}")
                        except:
                            error_message = "Bad request - Check API request format"
                        raise requests.exceptions.HTTPError(f"Claude API error (400): {error_message}")
                    elif response.status_code == 429:
                        raise requests.exceptions.HTTPError(f"Claude API rate limit exceeded (429): Too many requests")
                    elif response.status_code >= 500:
                        raise requests.exceptions.HTTPError(f"Claude API server error ({response.status_code}): Service unavailable")
                    else:
                        raise requests.exceptions.HTTPError(f"Claude API error ({response.status_code}): {error_detail}")
                
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON response from Claude API: {response.text[:200]}...")
                    raise ValueError("Invalid JSON response from Claude API")
                
                # Create response dict
                response_data = {
                    "content": result["content"][0]["text"],
                    "model": result.get("model", model),
                    "usage": {
                        "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                        "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": result.get("usage", {}).get("input_tokens", 0) + 
                                      result.get("usage", {}).get("output_tokens", 0)
                    },
                    "stop_reason": result.get("stop_reason", None)
                }
                
                # Fix JSON response if using structured output
                if structured_output:
                    content = response_data["content"]
                    logger.debug(f"Raw structured output response: {content[:100]}...")
                    
                    # Fix various JSON format issues
                    if content.startswith('{') and not content.startswith('{"'):
                        # Fix {fieldname" format to {"fieldname"
                        field_end = content.find('"')
                        if field_end > 1:
                            field_name = content[1:field_end]
                            fixed_content = '{"' + field_name + content[field_end:]
                            response_data["content"] = fixed_content
                            logger.debug(f"Fixed JSON format: {field_name} -> \"{field_name}\"")
                    elif not content.startswith('{'):
                        # For cases missing opening brace
                        response_data["content"] = '{' + content
                        logger.debug("Added missing opening brace to JSON response")
                
                # Cache the response if caching is enabled and the temperature is low enough
                if use_cache and temperature < 0.2:
                    llm_cache.set(system_prompt, user_prompt, model, response_data)
                
                logger.info(f"Claude API request successful. Token usage: {response_data['usage']}")
                return response_data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All Claude API request attempts failed")
        
        # This should never be reached due to the raise in the loop
        raise RuntimeError("Failed to get response from Claude API after multiple attempts")


class UnifiedLLMClient(BaseLLMClient):
    """
    Unified LLM client that tries multiple providers in order of preference.
    Falls back to alternative providers if the primary one fails.
    """
    
    def __init__(self, debug_mode=None, preferred_provider='deepseek'):
        """
        Initialize the unified LLM client.
        
        Args:
            debug_mode: Override debug mode (default: read from settings.DEBUG_LLM)
            preferred_provider: The preferred LLM provider ('deepseek' or 'claude')
        """
        super().__init__(debug_mode)
        self.preferred_provider = preferred_provider.lower()
        
        # Create clients for each provider
        try:
            self.deepseek_client = DeepSeekClient(debug_mode)
            self.has_deepseek = True
        except ValueError:
            logger.warning("DeepSeek API key not found, DeepSeek provider will be unavailable")
            self.has_deepseek = False
            
        try:
            self.claude_client = ClaudeClient(debug_mode)
            self.has_claude = True
        except ValueError:
            logger.warning("Claude API key not found, Claude provider will be unavailable")
            self.has_claude = False
            
        # Check if we have at least one provider
        if not (self.has_deepseek or self.has_claude) and not self.debug_mode:
            raise ValueError("No LLM providers available. Please configure at least one API key.")
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        structured_output: Dict = None,
        use_cache: bool = True,
        provider: str = None
    ) -> Dict:
        """
        Send a prompt to the preferred LLM provider and get a response.
        Falls back to alternative providers if the preferred one fails.
        
        Args:
            system_prompt: Instructions for the LLM on how to respond
            user_prompt: The content to respond to
            model: LLM model to use (provider-specific)
            max_tokens: Maximum response length
            temperature: Randomness parameter (0-1)
            structured_output: JSON schema for structured output (optional)
            use_cache: Whether to use the cache (default True)
            provider: Override the preferred provider for this request
            
        Returns:
            Dict containing the response text and metadata
        """
        # Determine which provider to use
        provider = provider.lower() if provider else self.preferred_provider
        
        # Debug mode can skip the availability checks
        if self.debug_mode:
            if provider == 'deepseek':
                return self.deepseek_client.generate_response(
                    system_prompt, user_prompt, model, max_tokens, 
                    temperature, structured_output, use_cache
                )
            else:
                return self.claude_client.generate_response(
                    system_prompt, user_prompt, model, max_tokens, 
                    temperature, structured_output, use_cache
                )
        
        # Try the preferred provider first
        errors = []
        
        if provider == 'deepseek' and self.has_deepseek:
            try:
                return self.deepseek_client.generate_response(
                    system_prompt, user_prompt, model, max_tokens, 
                    temperature, structured_output, use_cache
                )
            except Exception as e:
                logger.warning(f"DeepSeek API request failed: {str(e)}")
                errors.append(f"DeepSeek error: {str(e)}")
                # Fall back to Claude
                if self.has_claude:
                    logger.info("Falling back to Claude API")
                    provider = 'claude'
                else:
                    raise RuntimeError(f"DeepSeek API failed and no fallback available: {str(e)}")
        
        if provider == 'claude' and self.has_claude:
            try:
                return self.claude_client.generate_response(
                    system_prompt, user_prompt, model, max_tokens, 
                    temperature, structured_output, use_cache
                )
            except Exception as e:
                logger.warning(f"Claude API request failed: {str(e)}")
                errors.append(f"Claude error: {str(e)}")
                # Fall back to DeepSeek if we haven't tried it yet
                if self.has_deepseek and 'deepseek' not in [err.startswith('DeepSeek') for err in errors]:
                    logger.info("Falling back to DeepSeek API")
                    return self.deepseek_client.generate_response(
                        system_prompt, user_prompt, model, max_tokens, 
                        temperature, structured_output, use_cache
                    )
                    
        # If we get here, all available providers failed or none were available
        error_msg = "; ".join(errors) if errors else "No LLM providers available"
        raise RuntimeError(f"All LLM providers failed: {error_msg}")


# Instantiate the clients for use in other functions
deepseek_client = DeepSeekClient()
claude_client = ClaudeClient()

# Create a unified client with DeepSeek as the preferred provider
# Get preferred provider from settings, default to DeepSeek
preferred_provider = getattr(settings, 'DEFAULT_LLM_PROVIDER', 'deepseek').lower()
llm_client = UnifiedLLMClient(preferred_provider=preferred_provider)

def format_property_data(property_obj: Property) -> Dict[str, Any]:
    """
    Format property data for use in LLM prompts.
    
    Args:
        property_obj: The Property object to format
        
    Returns:
        Formatted property data dictionary
    """
    # Get all reviews for this property
    reviews = Review.objects.filter(booking__property=property_obj)
    
    review_data = []
    for review in reviews:
        review_data.append({
            "rating": float(review.rating),
            "rating": float(review.rating),
            "comment": review.comment,
            "date": review.created_at.strftime("%Y-%m-%d")
        })
    
    # Get amenities for this property - fixed to handle ManyToMany relationship correctly
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
        "reviews": review_data,
        "review_count": len(review_data),
        "average_rating": float(sum(r["rating"] for r in review_data) / len(review_data)) if review_data else None
    }

def format_user_data(user: User) -> Dict[str, Any]:
    """
    Format user data for use in LLM prompts.
    
    Args:
        user: The User object to format
        
    Returns:
        Formatted user data dictionary
    """
    # Get bookings made by this user
    bookings = user.bookings.all()
    
    booking_history = []
    for booking in bookings:
        booking_history.append({
            "property_id": booking.property.id,
            "property_title": booking.property.title,
            "property_type": booking.property.property_type,
            "location": f"{booking.property.city}, {booking.property.country}",
            "start_date": booking.start_date.strftime("%Y-%m-%d"),
            "end_date": booking.end_date.strftime("%Y-%m-%d"),
            "duration_days": (booking.end_date - booking.start_date).days,
            "has_review": hasattr(booking, 'review')
        })
    
    # Get all saved/favorite properties
    # Assuming there's a many-to-many relationship for favorites
    favorite_properties = []
    if hasattr(user, 'favorites'):
        for fav in user.favorites.all():
            favorite_properties.append({
                "id": fav.property.id,
                "title": fav.property.title,
                "property_type": fav.property.property_type,
                "location": f"{fav.property.city}, {fav.property.country}"
            })
    
    # Get travel preferences from the user profile
    travel_preferences = ""
    if hasattr(user, 'profile') and user.profile.travel_preferences:
        travel_preferences = user.profile.travel_preferences
    
    return {
        "id": user.id,
        "username": user.username,
        "user_type": user.user_type,
        "joined_date": user.date_joined.strftime("%Y-%m-%d"),
        "bookings": booking_history,
        "booking_count": len(booking_history),
        "favorites": favorite_properties,
        "favorite_count": len(favorite_properties),
        "travel_preferences": travel_preferences
    }

def parse_string_array(text: str) -> list:
    """Extract strings from a potential array text using regex"""
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
    Reconstruct JSON from Claude's text output when standard JSON parsing fails.
    Uses regex pattern matching to extract structured data.
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

def fix_json_format(content: str) -> str:
    """Apply comprehensive fixes to make JSON parseable"""
    logger.debug(f"Attempting to fix JSON format: {content[:100]}...")
    
    # Step 1: Check if we need to add the opening brace
    if not content.startswith('{'):
        content = '{' + content
        logger.debug("Added missing opening brace")
    
    # Step 2: Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Step 3: Replace single quotes with double quotes
    content = content.replace("'", '"')
    
    # Try the basic fixes first
    try:
        json_obj = json.loads(content)
        logger.debug("JSON parsed successfully without advanced fixes")
        return content
    except json.JSONDecodeError as e:
        logger.debug(f"Initial JSON parsing error (attempt 1): {str(e)}")
        
        # Step 4: Advanced fix for missing quotes around property names
        if "Expecting property name enclosed in double quotes" in str(e):
            try:
                # More sophisticated property name fix using regex
                import re
                
                # Find property names without quotes and add them
                pattern = r'{(\s*?)([a-zA-Z0-9_]+)(\s*?):'
                content = re.sub(pattern, r'{\1"\2"\3:', content)
                
                # Handle property names after commas
                pattern = r',(\s*?)([a-zA-Z0-9_]+)(\s*?):'
                content = re.sub(pattern, r',\1"\2"\3:', content)
                
                # Try parsing again after regex fixes
                try:
                    json_obj = json.loads(content)
                    logger.debug("JSON fixed successfully with regex")
                    return content
                except json.JSONDecodeError as e2:
                    logger.debug(f"JSON parsing still failed after regex fixes (attempt 2): {str(e2)}")
            except Exception as regex_error:
                logger.debug(f"Error during regex fix: {str(regex_error)}")
        
        # Step 5: Most aggressive fix - use a complete regex-based approach
        try:
            # Extract all property-value patterns and reconstruct with proper formatting
            import re
            
            # Create a list to hold properly formatted key-value pairs
            formatted_pairs = []
            
            # Extract property-value pairs using regex
            # This pattern tries to match both quoted and unquoted property names
            pairs_pattern = r'(?:,|\{)\s*(?:"([^"]+)"|([a-zA-Z0-9_]+))\s*:\s*(?:"([^"]*)"|\{([^}]*)\}|\[([^\]]*)\]|([^,}]*))'
            matches = re.finditer(pairs_pattern, content)
            
            for match in matches:
                # Get the property name (either quoted or unquoted)
                prop_name = match.group(1) if match.group(1) else match.group(2)
                
                # Get the value (various formats)
                if match.group(3):  # String value
                    value = f'"{match.group(3)}"'
                elif match.group(4):  # Object value
                    value = f"{{{match.group(4)}}}"
                elif match.group(5):  # Array value
                    value = f"[{match.group(5)}]"
                else:  # Other value (number, boolean, etc.)
                    value = match.group(6).strip()
                
                # Add the properly formatted pair
                formatted_pairs.append(f'"{prop_name}": {value}')
            
            # Reconstruct the JSON
            fixed_content = "{\n" + ",\n".join(formatted_pairs) + "\n}"
            
            # Try parsing one more time
            try:
                json_obj = json.loads(fixed_content)
                logger.debug("JSON fixed successfully with complete reconstruction")
                return fixed_content
            except json.JSONDecodeError as e3:
                logger.debug(f"Complete JSON reconstruction failed (attempt 3): {str(e3)}")
        except Exception as advanced_error:
            logger.debug(f"Error during advanced JSON fixing: {str(advanced_error)}")
    
    # If all fixes fail, return the original with some basic fixes
    logger.debug("All JSON fixing attempts failed, returning basic fixes only")
    
    # Last resort basic fixes
    if not content.startswith('{"'):
        # Try to add quotes around property names
        content = content.replace('{', '{"')
        content = content.replace(':', '":')
        content = content.replace(',', ',"')
        # Fix double quotes created by our replacements
        content = content.replace('""', '"')
    
    return content

def generate_property_summary(property_obj: Property) -> Dict:
    """
    Generate a summary of a property using the LLM.
    
    Args:
        property_obj: The Property object to summarize
        
    Returns:
        Dict containing summary text and highlights, with an additional "created_by" field
        indicating the generation method (e.g., "claude", "claude-fixed", "regex-extraction", "fallback")
    """
    # Format property data for the prompt
    property_data = format_property_data(property_obj)
    
    # System prompt with instructions for the LLM
    system_prompt = """
    You are an expert real estate copywriter for a rental platform. Your task is to create engaging and 
    accurate summaries of rental properties based on the provided data. 
    
    Please focus on:
    1. The most distinctive features of the property
    2. Location highlights and convenience
    3. Special amenities that make the property attractive
    4. The general atmosphere and style of the property
    
    The summary should be concise (100-150 words) but compelling, highlighting the property's 
    unique selling points. If reviews are available, incorporate insights from them.
    
    Return your response as a valid JSON object with the following structure:
    {
        "summary": "The engaging property summary text",
        "highlights": ["Key feature 1", "Key feature 2", "Key feature 3", "Key feature 4"]
    }
    
    The "highlights" should be a list of 3-5 short bullet points (5-8 words each) that highlight 
    the most appealing aspects of the property.
    
    IMPORTANT: Make sure to use proper JSON syntax with double quotes around all property names and string values.
    Do not include any explanation text outside of the JSON object.
    """
    
    # Prepare user prompt with property data
    user_prompt = f"""
    Please generate a compelling summary and highlights for the following property:
    
    {json.dumps(property_data, indent=2)}
    """
    
    # Define output schema for structured JSON response
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "highlights": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["summary", "highlights"]
    }
    
    # Get an instance of the unified LLM client
    llm_client = UnifiedLLMClient(preferred_provider='claude')
    
    # Maximum attempts for generating and parsing the response
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Generating property summary (attempt {attempt+1}/{max_attempts}) for property ID {property_obj.id}")
            
            # Add more detailed logging about the request
            logger.debug(f"System prompt: {system_prompt[:100]}...")
            logger.debug(f"User prompt: {user_prompt[:100]}...")
            
            response = llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                structured_output=schema,
                temperature=0.7,
                max_tokens=800
            )
            
            # Get the content from the response
            content = response["content"]
            logger.info(f"Raw property summary response (first 100 chars): {content[:100]}...")
            
            # Log the full response for debugging
            logger.debug(f"Full Claude API response: {json.dumps(response, indent=2)}")
            
            # Multi-level JSON parsing approach
            try:
                # Level 1: Direct parsing - try parsing as is
                result = json.loads(content)
                logger.info(f"Successfully generated property summary for property ID {property_obj.id}")
                
                # Ensure both required fields are present
                if "summary" not in result:
                    logger.warning(f"Summary field missing from LLM response for property ID {property_obj.id}")
                    if "highlights" in result:
                        # Create a summary from the highlights
                        highlights_text = ", ".join(result["highlights"])
                        result["summary"] = f"A {property_obj.property_type} in {property_obj.city} featuring {highlights_text}."
                        logger.info(f"Created summary from highlights: {result['summary']}")
                
                if "highlights" not in result:
                    logger.warning(f"Highlights field missing from LLM response for property ID {property_obj.id}")
                    # Create default highlights
                    result["highlights"] = [
                        f"{property_obj.bedroom_count} bedroom {property_obj.property_type}",
                        f"Located in {property_obj.city}",
                        "Modern amenities and comfort"
                    ]
                    logger.info(f"Created default highlights: {result['highlights']}")
                
                # Add created_by field to indicate generation method
                result["created_by"] = "claude"
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parsing error (attempt {attempt+1}): {str(e)}")
                logger.debug(f"JSON parsing error details: {str(e)}, content: {content}")
                
                # Level 2: Try with basic JSON fixes
                logger.info("Attempting to fix JSON...")
                fixed_content = fix_json_format(content)
                
                try:
                    # Try parsing with fixed JSON
                    result = json.loads(fixed_content)
                    logger.info(f"Successfully parsed property summary JSON after fixes for property ID {property_obj.id}")
                    
                    # Ensure both required fields are present
                    if "summary" not in result:
                        logger.warning(f"Summary field missing from fixed LLM response for property ID {property_obj.id}")
                        if "highlights" in result:
                            # Create a summary from the highlights
                            highlights_text = ", ".join(result["highlights"])
                            result["summary"] = f"A {property_obj.property_type} in {property_obj.city} featuring {highlights_text}."
                            logger.info(f"Created summary from highlights: {result['summary']}")
                    
                    if "highlights" not in result:
                        logger.warning(f"Highlights field missing from fixed LLM response for property ID {property_obj.id}")
                        # Create default highlights
                        result["highlights"] = [
                            f"{property_obj.bedroom_count} bedroom {property_obj.property_type}",
                            f"Located in {property_obj.city}",
                            "Modern amenities and comfort"
                        ]
                        logger.info(f"Created default highlights: {result['highlights']}")
                    
                    # Add created_by field to indicate generation method
                    result["created_by"] = "claude-fixed"
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing still failed after basic fixes (attempt {attempt+1}): {str(e)}")
                    logger.debug(f"After fix, JSON parsing error details: {str(e)}, content: {fixed_content}")
                    
                    # Level 3: Regex-based extraction for complex failures
                    logger.info("Attempting regex-based JSON extraction...")
                    
                    # Extract summary using regex
                    summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', fixed_content, re.DOTALL)
                    highlights_match = re.search(r'"highlights"\s*:\s*\[(.*?)\]', fixed_content, re.DOTALL)
                    
                    # Initialize result dictionary
                    result = {}
                    
                    # Extract and add summary if found
                    if summary_match:
                        result["summary"] = summary_match.group(1)
                    else:
                        # Create a default summary if not found
                        result["summary"] = f"A {property_obj.property_type} in {property_obj.city} with {property_obj.bedroom_count} bedrooms."
                        logger.info(f"Created default summary: {result['summary']}")
                    
                    # Extract and add highlights if found
                    if highlights_match:
                        highlights_text = highlights_match.group(1)
                        highlights = re.findall(r'"([^"]+)"', highlights_text)
                        if highlights:
                            result["highlights"] = highlights
                        else:
                            # Create default highlights if extraction failed
                            result["highlights"] = [
                                f"{property_obj.bedroom_count} bedroom {property_obj.property_type}",
                                f"Located in {property_obj.city}",
                                "Modern amenities and comfort"
                            ]
                            logger.info(f"Created default highlights: {result['highlights']}")
                    else:
                        # Create default highlights if not found
                        result["highlights"] = [
                            f"{property_obj.bedroom_count} bedroom {property_obj.property_type}",
                            f"Located in {property_obj.city}",
                            "Modern amenities and comfort"
                        ]
                        logger.info(f"Created default highlights: {result['highlights']}")
                    
                    logger.info(f"Successfully extracted property summary using regex for property ID {property_obj.id}")
                    result["created_by"] = "regex-extraction"
                    return result
                    
                    # Try again if this isn't the last attempt
                    if attempt < max_attempts - 1:
                        logger.info(f"Retrying property summary generation (attempt {attempt+1}/{max_attempts})")
                        continue
                    # Otherwise, fall through to the fallback response
                
        except Exception as e:
            # More detailed error logging
            logger.error(f"Error generating property summary (attempt {attempt+1}): {str(e)}")
            logger.error(f"Error type: {type(e).__name__}, Error details: {str(e)}")
            
            # If this is the last attempt, we'll fall through to the fallback response
            if attempt < max_attempts - 1:
                logger.info(f"Retrying property summary generation after error (attempt {attempt+1}/{max_attempts})")
                continue
    
    # If we've exhausted all attempts, use the fallback
    logger.warning(f"Using fallback property summary for property ID {property_obj.id} after {max_attempts} failed attempts")
    
    # In debug mode (development), use fallback but log this extensively
    is_debug = getattr(settings, 'DEBUG', False)
    if is_debug:
        logger.warning("Using fallback response because DEBUG=True. In production, this error would be raised.")
        logger.warning("Set DEBUG=False to see the actual error or DEBUG_LLM=True to use mock responses instead.")
        
        # Fallback response for development/debug mode
        return {
            "summary": f"A lovely {property_obj.property_type} located in {property_obj.city}, {property_obj.country}. (Note: This is fallback data due to API error)",
            "highlights": [
                f"{property_obj.bedroom_count} bedroom accommodation",
                f"Located in {property_obj.city}",
                "Comfortable and convenient",
                "FALLBACK DATA - API ERROR"
            ],
            "created_by": "fallback"
        }
    else:
        # In production, we should raise the error
        raise RuntimeError(f"Failed to generate property summary after {max_attempts} attempts")

def generate_user_persona(user: User) -> Dict:
    """
    Generate a persona for a user based on their behavior and preferences.
    
    Args:
        user: The User object to create a persona for
        
    Returns:
        Dict containing the persona data
    """
    # Format user data for the prompt
    user_data = format_user_data(user)
    
    # System prompt with instructions for the LLM
    system_prompt = """
    You are an expert in user behavior analysis for a rental platform. Your task is to generate 
    a comprehensive persona for a user based on their booking history, favorite properties, and other data.
    
    Pay special attention to the user's stated travel_preferences if provided. This is the user's self-described
    travel style and preferences in their own words, and should heavily influence your analysis.
    
    Create a detailed persona that includes:
    1. Travel preferences (trip types, typical duration, preferred locations)
    2. Accommodation preferences (property types, amenities, price sensitivity)
    3. Booking patterns (advance booking time, seasonality, group size)
    4. Predicted preferences for properties they might like in the future
    
    Return your response as a valid JSON object with the following structure:
    {
        "preferences": {
            "property_types": ["Apartment", "House", etc.],
            "locations": ["Urban centers", "Beach destinations", etc.],
            "amenities": ["WiFi", "Kitchen", etc.],
            "price_range": "budget-conscious" or "mid-range" or "luxury-oriented",
            "travel_style": ["Leisure", "Business", "Family", etc.]
        },
        "travel_habits": {
            "typical_group_size": "solo" or "couples" or "family" or "large groups",
            "typical_stay_length": "weekend getaways" or "extended stays" or "mix of durations",
            "booking_frequency": "frequent" or "occasional" or "rare",
            "planning_style": "last-minute" or "1-2 weeks ahead" or "months ahead"
        },
        "interests": ["Outdoor activities", "Cultural experiences", "Food and dining", etc.],
        "model": "claude-3-sonnet",
        "created_by": "claude"
    }
    
    Base your analysis entirely on the provided data, especially the user's stated travel_preferences if available.
    If data is limited, make reasonable inferences but indicate when you're making an assumption with lower confidence.
    """
    
    # Prepare user prompt with user data
    user_prompt = f"""
    Please generate a comprehensive user persona based on the following user data:
    
    {json.dumps(user_data, indent=2)}
    """
    
    # Define output schema for structured JSON response
    schema = {
        "type": "object",
        "properties": {
            "preferences": {
                "type": "object",
                "properties": {
                    "property_types": {"type": "array", "items": {"type": "string"}},
                    "locations": {"type": "array", "items": {"type": "string"}},
                    "amenities": {"type": "array", "items": {"type": "string"}},
                    "price_range": {"type": "string"},
                    "travel_style": {"type": "array", "items": {"type": "string"}}
                }
            },
            "travel_habits": {
                "type": "object",
                "properties": {
                    "typical_group_size": {"type": "string"},
                    "typical_stay_length": {"type": "string"},
                    "booking_frequency": {"type": "string"},
                    "planning_style": {"type": "string"}
                }
            },
            "interests": {"type": "array", "items": {"type": "string"}},
            "model": {"type": "string"},
            "created_by": {"type": "string"}
        }
    }
    
    try:
        response = llm_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            structured_output=schema,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the structured JSON response
        result = json.loads(response["content"])
        return result
        
    except Exception as e:
        logger.error(f"Error generating user persona: {str(e)}")
        # Fallback response if the API call fails
        return {
            "preferences": {
                "property_types": ["Apartment"],
                "locations": ["Urban destinations", "Popular tourist spots"],
                "amenities": ["WiFi", "Kitchen"],
                "price_range": "mid-range",
                "travel_style": ["Leisure"]
            },
            "travel_habits": {
                "typical_group_size": "couples",
                "typical_stay_length": "weekend getaways",
                "booking_frequency": "occasional",
                "planning_style": "1-2 weeks ahead"
            },
            "interests": ["Cultural experiences", "Food and dining"],
            "model": "claude-3-sonnet",
            "created_by": "fallback"
        }

def generate_property_persona(property_obj: Property) -> Dict:
    """
    Generate a persona for a property based on its characteristics and reviews.
    
    Args:
        property_obj: The Property object to create a persona for
        
    Returns:
        Dict containing the persona data with an additional "created_by" field 
        indicating the generation method (e.g., "claude", "regex-extraction", "fallback")
    """
    # Format property data for the prompt
    property_data = format_property_data(property_obj)
    
    # System prompt with instructions for the LLM
    system_prompt = """
    You are an expert in real estate market analysis for a rental platform. Your task is to generate 
    a comprehensive persona for a property based on its characteristics, amenities, location, and reviews.
    
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
    Base your analysis entirely on the provided data. If data is limited, make reasonable inferences 
    but indicate when you're making an assumption with lower confidence.
    """
    
    # Prepare user prompt with property data
    user_prompt = f"""
    Please generate a comprehensive property persona based on the following property data:
    
    {json.dumps(property_data, indent=2)}
    """
    
    # Define output schema for structured JSON response
    schema = {
        "type": "object",
        "properties": {
            "ideal_guests": {
                "type": "object",
                "properties": {
                    "demographics": {"type": "array", "items": {"type": "string"}},
                    "traveler_types": {"type": "array", "items": {"type": "string"}}
                }
            },
            "use_cases": {
                "type": "object",
                "properties": {
                    "primary": {"type": "array", "items": {"type": "string"}},
                    "secondary": {"type": "array", "items": {"type": "string"}}
                }
            },
            "unique_attributes": {
                "type": "object",
                "properties": {
                    "key_selling_points": {"type": "array", "items": {"type": "string"}},
                    "stand_out_amenities": {"type": "array", "items": {"type": "string"}}
                }
            },
            "atmosphere": {
                "type": "object",
                "properties": {
                    "overall_vibe": {"type": "string"},
                    "descriptors": {"type": "array", "items": {"type": "string"}}
                }
            },
            "market_position": {
                "type": "object",
                "properties": {
                    "property_class": {"type": "string"},
                    "comparable_to": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
    
    # Get an instance of the unified LLM client
    llm_client = UnifiedLLMClient(preferred_provider='claude')
    
    # Maximum attempts for generating and parsing the response
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Generating property persona (attempt {attempt+1}/{max_attempts})")
            
            response = llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                structured_output=schema,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Get the content from the response
            content = response["content"]
            logger.debug(f"Raw property persona response: {content[:100]}...")
            
            # Multi-level JSON parsing approach
            try:
                # Level 1: Direct parsing - try parsing as is
                result = json.loads(content)
                logger.info(f"Successfully generated property persona for property ID {property_obj.id}")
                # Add created_by field to indicate generation method
                result["created_by"] = "claude"
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parsing error (attempt {attempt+1}): {str(e)}")
                
                # Level 2: Try with basic JSON fixes
                logger.debug("Attempting to fix JSON...")
                fixed_content = fix_json_format(content)
                
                try:
                    # Try parsing with fixed JSON
                    result = json.loads(fixed_content)
                    logger.info(f"Successfully parsed property persona JSON after fixes for property ID {property_obj.id}")
                    # Add created_by field to indicate generation method
                    result["created_by"] = "claude-fixed"
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing still failed after basic fixes (attempt {attempt+1}): {str(e)}")
                    
                    # Level 3: Regex-based extraction for complex failures
                    logger.debug("Attempting regex-based JSON extraction...")
                    result = reconstruct_json_from_claude(content)
                    
                    # Validate the extracted structure
                    required_keys = ["ideal_guests", "use_cases", "unique_attributes", "atmosphere", "market_position"]
                    missing_keys = [key for key in required_keys if key not in result]
                    
                    if not missing_keys:
                        logger.info(f"Successfully extracted property persona using regex for property ID {property_obj.id}")
                        # Add created_by field to indicate generation method
                        result["created_by"] = "regex-extraction"
                        return result
                    else:
                        logger.warning(f"Incomplete regex extraction, missing keys: {missing_keys}")
                        # Try again if this isn't the last attempt
                        if attempt < max_attempts - 1:
                            continue
                        # Otherwise, fall through to the fallback response
                
        except Exception as e:
            logger.error(f"Error generating property persona (attempt {attempt+1}): {str(e)}")
            # If this is the last attempt, we'll fall through to the fallback response
            if attempt < max_attempts - 1:
                continue
    
    # If we've exhausted all attempts, use the fallback
    logger.warning(f"Using fallback property persona for property ID {property_obj.id} after {max_attempts} failed attempts")
    
    # Check if this is a production environment before using fallback
    if not getattr(settings, 'DEBUG', False):
        # In production, we should raise the error
        raise RuntimeError(f"Failed to generate property persona after {max_attempts} attempts")
    
    # Fallback response (for development/debug mode)
    return {
        "ideal_guests": {
            "demographics": ["Young professionals", "Couples"],
            "traveler_types": ["Leisure travelers", "Vacationers"]
        },
        "use_cases": {
            "primary": ["Vacation stays", "Weekend getaways"],
            "secondary": ["Extended trips", "Special occasions"]
        },
        "unique_attributes": {
            "key_selling_points": [f"Located in {property_obj.city}", f"{property_obj.bedroom_count} bedroom accommodation"],
            "stand_out_amenities": ["Comfortable living space", "Note: This is fallback data due to API error"]
        },
        "atmosphere": {
            "overall_vibe": "comfortable and welcoming",
            "descriptors": ["Cozy", "Convenient", "Pleasant", "FALLBACK DATA"]
        },
        "market_position": {
            "property_class": "mid-range",
            "comparable_to": ["Standard hotel rooms", "Vacation rentals"]
        },
        "created_by": "fallback"
    }

def generate_recommendations(user: User, limit: int = 5) -> List[Dict]:
    """
    Generate personalized property recommendations for a user.
    
    Args:
        user: The User object to generate recommendations for
        limit: Maximum number of recommendations to return
        
    Returns:
        List of recommendation dictionaries with property info and match reasons
    """
    from properties.models import Property
    
    # Format user data for the prompt
    user_data = format_user_data(user)
    
    # Get properties that aren't owned by the user
    # and that the user hasn't already booked
    booked_property_ids = [b["property_id"] for b in user_data["bookings"]]
    available_properties = Property.objects.exclude(leaser=user).exclude(id__in=booked_property_ids)[:10]
    
    # Format available properties for recommendation
    property_options = []
    for prop in available_properties:
        property_options.append(format_property_data(prop))
    
    # If no properties are available, return empty recommendations
    if not property_options:
        return []
    
    # System prompt with instructions for the LLM
    system_prompt = """
    You are an expert recommendation system for a rental platform. Your task is to analyze a user's 
    booking history and preferences, then recommend suitable properties from a list of available options.
    
    For each recommendation, explain WHY this property would appeal to the user based on their history and preferences.
    Focus on specific features, location, amenities, or other factors that match what the user has shown interest in.
    
    Return your response as a valid JSON array of recommendation objects with the following structure:
    [
        {
            "property_id": 123,
            "match_score": 92,
            "match_reasons": [
                "Matches your preference for beachfront properties",
                "Has the full kitchen you typically look for",
                "Similar to the property you stayed at in Miami"
            ]
        },
        ...more recommendations...
    ]
    
    Where:
    - property_id matches the ID from the available properties list
    - match_score is a percentage between 50-100 indicating how well the property matches the user's preferences
    - match_reasons is a list of 2-4 specific reasons why this property would appeal to this user
    
    Sort the recommendations by match_score in descending order and limit to the 5 best matches.
    If there isn't enough user data to make confident recommendations, base your recommendations on 
    what seems most appealing in general and note this in the match_reasons.
    """
    
    # Prepare user prompt with user data and property options
    user_prompt = f"""
    Please recommend properties for the following user based on their profile and the available options:
    
    USER PROFILE:
    {json.dumps(user_data, indent=2)}
    
    AVAILABLE PROPERTIES:
    {json.dumps(property_options, indent=2)}
    """
    
    # Define output schema for structured JSON response
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "match_score": {"type": "integer"},
                "match_reasons": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["property_id", "match_score", "match_reasons"]
        }
    }
    
    try:
        response = llm_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            structured_output=schema,
            temperature=0.7,
            max_tokens=1500
        )
        
        # Parse the structured JSON response
        recommendations = json.loads(response["content"])
        
        # Limit to requested number
        return recommendations[:limit]
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        # Fallback response if the API call fails
        fallback_recommendations = []
        for i, prop in enumerate(available_properties[:limit]):
            fallback_recommendations.append({
                "property_id": prop.id,
                "match_score": 85 - (i * 5),  # Decreasing scores
                "match_reasons": [
                    f"Highly-rated {prop.property_type} in {prop.city}",
                    "Features amenities you might enjoy",
                    "Popular with similar travelers"
                ]
            })
        return fallback_recommendations 