import os
import sys
import json
import logging
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

# Make sure we can import from llm_services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import the UnifiedLLMClient
from llm_services.services.llm_client import UnifiedLLMClient, ClaudeClient

def test_claude_direct():
    """Test Claude API directly"""
    logger.info("Testing Claude API directly")
    
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return False
    
    logger.info(f"API Key found: {api_key[:4]}...{api_key[-4:]}")
    
    # Initialize Claude client
    claude_client = ClaudeClient(api_key=api_key)
    
    # Test with a simple prompt
    prompt = "Hello, I'm testing the Claude API. Please respond with a short greeting."
    
    logger.info(f"Sending prompt to Claude API: {prompt}")
    
    try:
        response = claude_client.generate_response(prompt)
        logger.info(f"Claude API Response: {response}")
        return True
    except Exception as e:
        logger.error(f"Error with Claude API: {str(e)}")
        return False

def test_unified_client_claude():
    """Test the UnifiedLLMClient with Claude as provider"""
    logger.info("Testing UnifiedLLMClient with Claude provider")
    
    # Initialize the UnifiedLLMClient with Claude as provider
    client = UnifiedLLMClient(provider="claude")
    
    # Test with a simple prompt
    prompt = "Hello, I'm testing the Unified LLM Client with Claude. Please respond with a short greeting."
    
    logger.info(f"Sending prompt to UnifiedLLMClient (Claude): {prompt}")
    
    try:
        response = client.generate_response(prompt)
        logger.info(f"UnifiedLLMClient (Claude) Response: {response}")
        return True
    except Exception as e:
        logger.error(f"Error with UnifiedLLMClient (Claude): {str(e)}")
        return False

def print_environment_variables():
    """Print relevant environment variables (with masked values)"""
    env_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "DJANGO_SETTINGS_MODULE": os.getenv("DJANGO_SETTINGS_MODULE"),
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
    success = test_claude_direct()
    if success:
        logger.info("✅ Claude API direct test successful")
    else:
        logger.info("❌ Claude API direct test failed")
    
    # Test UnifiedLLMClient with Claude
    success = test_unified_client_claude()
    if success:
        logger.info("✅ UnifiedLLMClient with Claude test successful")
    else:
        logger.info("❌ UnifiedLLMClient with Claude test failed") 