import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("claude_test")

# Load environment variables
load_dotenv()

def test_claude_api():
    """Test Claude API directly using requests"""
    logger.info("Testing Claude API directly")
    
    # Get API key from environment
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        logger.error("CLAUDE_API_KEY not found in environment variables")
        return False
    
    logger.info(f"API Key found: {api_key[:4]}...{api_key[-4:]}")
    
    # API endpoint and headers
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Create request payload
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 100,
        "temperature": 0.7,
        "system": "You are a helpful AI assistant that provides concise responses.",
        "messages": [
            {
                "role": "user",
                "content": "Hello, I'm testing the Claude API. Please respond with a short greeting."
            }
        ]
    }
    
    logger.info(f"API URL: {url}")
    logger.info(f"Headers: {json.dumps({k: v if k != 'x-api-key' else f'{v[:4]}...{v[-4:]}' for k, v in headers.items()})}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Log response status
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Check if successful
        if response.status_code == 200:
            resp_data = response.json()
            logger.info(f"Claude API Response: {json.dumps(resp_data, indent=2)}")
            logger.info(f"Content: {resp_data.get('content', [])}")
            return True
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error with Claude API request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def print_environment_variables():
    """Print relevant environment variables (with masked values)"""
    env_vars = {
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
    }
    
    logger.info("Environment Variables:")
    for key, value in env_vars.items():
        if value:
            if 'API_KEY' in key:
                # Mask API keys for security
                logger.info(f"  {key}: {value[:4]}...{value[-4:]}")
            else:
                logger.info(f"  {key}: {value}")
        else:
            logger.info(f"  {key}: Not set")

if __name__ == "__main__":
    print_environment_variables()
    
    # Test Claude directly
    success = test_claude_api()
    if success:
        logger.info("✅ Claude API direct test successful")
    else:
        logger.info("❌ Claude API direct test failed") 