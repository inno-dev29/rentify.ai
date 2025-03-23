"""
Test script for LLM services.
This script can be run manually to test the LLM API integration (DeepSeek and Claude).

Run it with:
    python manage.py shell < test_llm.py
    
To run with debug mode:
    DEBUG_LLM=True python manage.py shell < test_llm.py
"""

import os
import sys
import json
import time
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from django.conf import settings
from llm_services.services.llm_client import (
    DeepSeekClient, ClaudeClient, UnifiedLLMClient, 
    deepseek_client, claude_client, llm_client,
    generate_property_summary
)
from llm_services.services.cache import llm_cache
from properties.models import Property
from users.models import User

def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print(f"{'=' * 50}")

# Test the Unified LLM client
def test_unified_client():
    print_section("Testing Unified LLM Client")
    
    debug_status = "ENABLED" if getattr(settings, "DEBUG_LLM", False) else "DISABLED"
    print(f"Debug mode is {debug_status}")
    preferred_provider = getattr(settings, "DEFAULT_LLM_PROVIDER", "deepseek")
    print(f"Preferred provider: {preferred_provider}")
    
    system_prompt = "You are a helpful assistant that provides concise responses."
    user_prompt = "What are the top 3 tourist attractions in Paris? List them with a one-sentence description for each."
    
    try:
        print("\nTesting with default provider...")
        response = llm_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        print("Response received successfully!")
        if response.get("is_mock"):
            print("⚠️  This is a mock response from debug mode")
        print(f"Content: {response['content'][:200]}...")  # Print first 200 chars
        print(f"Model: {response.get('model', 'unknown')}")
        print(f"Usage: {response.get('usage', {})}")
        
        # Try with explicit provider specification
        if not getattr(settings, "DEBUG_LLM", False):
            alt_provider = "claude" if preferred_provider == "deepseek" else "deepseek"
            print(f"\nTesting with explicit provider ({alt_provider})...")
            try:
                alt_response = llm_client.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=500,
                    temperature=0.7,
                    provider=alt_provider
                )
                print(f"Alternative provider response: {alt_response['content'][:100]}...")
            except Exception as e:
                print(f"Alternative provider test failed: {str(e)}")
        
        return True
    except Exception as e:
        print(f"Error testing unified LLM client: {str(e)}")
        return False

# Test the DeepSeek client directly
def test_deepseek_client():
    print_section("Testing DeepSeek Client")
    
    debug_status = "ENABLED" if getattr(settings, "DEBUG_LLM", False) else "DISABLED"
    print(f"Debug mode is {debug_status}")
    
    system_prompt = "You are a helpful assistant that provides concise responses."
    user_prompt = "What makes DeepSeek LLM unique? Answer in three brief points."
    
    try:
        response = deepseek_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        print("Response received successfully!")
        if response.get("is_mock"):
            print("⚠️  This is a mock response from debug mode")
        print(f"Content: {response['content'][:200]}...")  # Print first 200 chars
        print(f"Model: {response.get('model', 'unknown')}")
        print(f"Usage: {response.get('usage', {})}")
        return True
    except Exception as e:
        print(f"Error testing DeepSeek client: {str(e)}")
        return False

# Test the Claude client directly
def test_claude_client():
    print_section("Testing Claude Client")
    
    debug_status = "ENABLED" if getattr(settings, "DEBUG_LLM", False) else "DISABLED"
    print(f"Debug mode is {debug_status}")
    
    system_prompt = "You are a helpful assistant that provides concise responses."
    user_prompt = "What are the top 3 tourist attractions in Paris? List them with a one-sentence description for each."
    
    try:
        response = claude_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        print("Response received successfully!")
        if response.get("is_mock"):
            print("⚠️  This is a mock response from debug mode")
        print(f"Content: {response['content'][:200]}...")  # Print first 200 chars
        print(f"Model: {response.get('model', 'unknown')}")
        print(f"Usage: {response.get('usage', {})}")
        return True
    except Exception as e:
        print(f"Error testing Claude client: {str(e)}")
        return False

# Test response caching
def test_caching():
    print_section("Testing Response Caching")
    
    system_prompt = "You are an assistant that provides factual information concisely."
    user_prompt = "What is the capital of France? Answer in one word."
    
    # We'll use the preferred provider for caching test
    client = llm_client
    model = "deepseek-chat"  # Default model for our DeepSeek client
    
    # Clear any existing cache entry for this prompt
    cache_key = llm_cache.get_cache_key(system_prompt, user_prompt, model)
    cache_file = os.path.join(llm_cache.cache_dir, f"{cache_key}.json")
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("Removed existing cache file for this query")
    
    # First request - should call the API or generate mock response
    print("\nMaking first request (not cached)...")
    start_time = time.time()
    response1 = client.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,  # Use 0 for deterministic responses that can be cached
        use_cache=True
    )
    time1 = time.time() - start_time
    print(f"First request took {time1:.3f} seconds")
    print(f"Response: {response1['content']}")
    
    # Second request - should use cache
    print("\nMaking second request (should use cache)...")
    start_time = time.time()
    response2 = client.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
        use_cache=True
    )
    time2 = time.time() - start_time
    print(f"Second request took {time2:.3f} seconds")
    print(f"Response: {response2['content']}")
    
    # Request without caching
    print("\nMaking third request (without cache)...")
    start_time = time.time()
    response3 = client.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
        use_cache=False  # Disable cache for this request
    )
    time3 = time.time() - start_time
    print(f"Third request took {time3:.3f} seconds")
    
    # Check if responses match
    responses_match = response1['content'] == response2['content']
    print(f"Do cached responses match? {'✅ Yes' if responses_match else '❌ No'}")
    
    # Check if cache is faster
    cache_is_faster = time2 < time1
    print(f"Is cache faster? {'✅ Yes' if cache_is_faster else '❌ No'} (Speed improvement: {(1 - time2/time1)*100:.1f}%)")
    
    return responses_match and cache_is_faster

# Test debug mode
def test_debug_mode():
    print_section("Testing Debug Mode")
    
    # Create clients with different debug settings
    debug_client = UnifiedLLMClient(debug_mode=True)
    prod_client = None
    
    # Only create a production client if we have at least one API key
    if getattr(settings, 'DEEPSEEK_API_KEY', '') or getattr(settings, 'CLAUDE_API_KEY', ''):
        prod_client = UnifiedLLMClient(debug_mode=False)
    
    system_prompt = "You are a helpful assistant."
    user_prompt = "Hello, how are you today?"
    
    # Test debug client
    print("\nTesting debug mode client:")
    try:
        debug_response = debug_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        print(f"Debug response: {debug_response['content'][:100]}...")
        print(f"Is mock: {debug_response.get('is_mock', False)}")
        
        # Make the same request again to verify deterministic mock responses
        debug_response2 = debug_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        responses_consistent = debug_response['content'] == debug_response2['content']
        print(f"Are mock responses consistent? {'✅ Yes' if responses_consistent else '❌ No'}")
        
        # Test production client if available
        if prod_client:
            print("\nTesting production mode client:")
            try:
                prod_response = prod_client.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt
                )
                print(f"Production response: {prod_response['content'][:100]}...")
                print(f"Is mock: {prod_response.get('is_mock', False)}")
                
                # Compare responses
                responses_different = debug_response['content'] != prod_response['content']
                print(f"Are debug and prod responses different? {'✅ Yes' if responses_different else '❌ No'}")
                
                return responses_consistent and responses_different
            except Exception as e:
                print(f"Error with production client: {str(e)}")
                return responses_consistent
        else:
            print("\nSkipping production client test (no API key)")
            return responses_consistent
    except Exception as e:
        print(f"Error testing debug mode: {str(e)}")
        return False

# Test property summary generation
def test_property_summary():
    print_section("Testing Property Summary Generation")
    
    # Get a sample property
    try:
        property_obj = Property.objects.first()
        if not property_obj:
            print("No properties found in the database. Please create a property first.")
            return False
        
        print(f"Generating summary for property: {property_obj.title}")
        summary = generate_property_summary(property_obj)
        
        print("Summary generated successfully!")
        print(f"Summary: {summary['summary'][:200]}...")  # Print first 200 chars
        print("Highlights:")
        for highlight in summary["highlights"]:
            print(f"- {highlight}")
        
        return True
    except Exception as e:
        print(f"Error testing property summary: {str(e)}")
        return False

if __name__ == "__main__":
    # Check environment
    print_section("Test Environment")
    print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Debug mode: {getattr(settings, 'DEBUG_LLM', False)}")
    print(f"DeepSeek API configured: {'✅ Yes' if getattr(settings, 'DEEPSEEK_API_KEY', '') else '❌ No'}")
    print(f"Claude API configured: {'✅ Yes' if getattr(settings, 'CLAUDE_API_KEY', '') else '❌ No'}")
    print(f"Default LLM provider: {getattr(settings, 'DEFAULT_LLM_PROVIDER', 'deepseek')}")
    print(f"Cache directory: {llm_cache.cache_dir}")
    
    # Run tests
    unified_test = test_unified_client()
    deepseek_test = test_deepseek_client()
    claude_test = test_claude_client()
    cache_test = test_caching()
    debug_test = test_debug_mode()
    summary_test = test_property_summary()
    
    # Print summary
    print_section("Test Results")
    print(f"Unified LLM Client: {'✅ PASSED' if unified_test else '❌ FAILED'}")
    print(f"DeepSeek Client: {'✅ PASSED' if deepseek_test else '❌ FAILED'}")
    print(f"Claude Client: {'✅ PASSED' if claude_test else '❌ FAILED'}")
    print(f"Response Caching: {'✅ PASSED' if cache_test else '❌ FAILED'}")
    print(f"Debug Mode: {'✅ PASSED' if debug_test else '❌ FAILED'}")
    print(f"Property Summary: {'✅ PASSED' if summary_test else '❌ FAILED'}")
    
    tests_passed = sum([unified_test, deepseek_test, claude_test, cache_test, debug_test, summary_test])
    tests_total = 6
    
    print(f"\n{tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        sys.exit(1) 