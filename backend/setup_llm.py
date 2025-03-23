"""
Setup script for LLM services.
This script helps users set up and test the Claude API integration.

Run it with:
    python setup_llm.py
"""

import os
import sys
import json
import subprocess
import re

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def check_env_file():
    """Check if .env file exists and contains the Claude API key."""
    print_header("Checking Environment Configuration")
    
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_file):
        print("⚠️  .env file not found")
        print("Creating a new .env file...")
        
        with open(env_file, 'w') as f:
            f.write("# Django settings\n")
            f.write("SECRET_KEY=django-insecure-zb=(xqd5t$udds^-f-nxqf1=1tz1o69(kzt3(q2%*j5*5z3e2g\n")
            f.write("DEBUG=True\n")
            f.write("ALLOWED_HOSTS=localhost,127.0.0.1\n")
            f.write("USE_SQLITE=True\n\n")
            f.write("# Claude API configuration\n")
            f.write("CLAUDE_API_KEY=\n")
        
        print("✅ Created .env file template")
    else:
        print("✅ .env file exists")
    
    # Check for Claude API key
    claude_key = None
    with open(env_file, 'r') as f:
        env_content = f.read()
        match = re.search(r'CLAUDE_API_KEY=([^\s]+)', env_content)
        if match:
            claude_key = match.group(1)
    
    if not claude_key:
        print("\n⚠️  CLAUDE_API_KEY not set in .env file")
        
        api_key = input("\nPlease enter your Claude API key (or press Enter to skip for now): ").strip()
        
        if api_key:
            # Update the .env file
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            if 'CLAUDE_API_KEY=' in env_content:
                env_content = re.sub(r'CLAUDE_API_KEY=([^\s]*)', f'CLAUDE_API_KEY={api_key}', env_content)
            else:
                env_content += f"\nCLAUDE_API_KEY={api_key}\n"
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            print("✅ Added Claude API key to .env file")
        else:
            print("⚠️  Skipped adding Claude API key")
            print("   Note: You'll need to add it later to use the LLM features")
    else:
        print("✅ Claude API key is configured")

def check_dependencies():
    """Check if required Python packages are installed."""
    print_header("Checking Dependencies")
    
    required_packages = {
        'requests': 'requests',
        'anthropic': 'anthropic'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("\nInstalling missing packages...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ All missing packages have been installed")
    else:
        print("✅ All required packages are already installed")

def test_claude_integration():
    """Test the Claude API integration with a simple request."""
    print_header("Testing Claude API Integration")
    
    try:
        # Import after potential installation
        import requests
        
        # Load API key from .env
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        api_key = None
        
        with open(env_file, 'r') as f:
            env_content = f.read()
            match = re.search(r'CLAUDE_API_KEY=([^\s]+)', env_content)
            if match:
                api_key = match.group(1)
        
        if not api_key:
            print("❌ Cannot test Claude API: API key not found in .env")
            return False
        
        # Simple test request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "system": "You are a helpful assistant that responds with short answers.",
            "messages": [
                {"role": "user", "content": "Say hello world!"}
            ],
            "max_tokens": 100,
            "temperature": 0
        }
        
        print("Sending test request to Claude API...")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nClaude says: {result['content'][0]['text']}")
            print("\n✅ Successfully connected to Claude API!")
            return True
        else:
            print(f"\n❌ API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing Claude API: {str(e)}")
        return False

def create_cache_directory():
    """Create cache directory for LLM responses."""
    print_header("Setting Up LLM Cache")
    
    cache_dir = os.path.join(os.path.dirname(__file__), '.llm_cache')
    
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        print(f"✅ Created cache directory at {cache_dir}")
    else:
        print(f"✅ Cache directory already exists at {cache_dir}")

def print_next_steps():
    """Print information about what to do next."""
    print_header("Next Steps")
    
    print("Your LLM integration is now set up. Here's what you can do next:")
    print()
    print("1. Run the test script to verify everything is working:")
    print("   python manage.py shell < test_llm.py")
    print()
    print("2. Start the Django development server:")
    print("   python manage.py runserver")
    print()
    print("3. Visit the API endpoints:")
    print("   - Property summaries: http://localhost:8000/api/properties/{id}/summary/")
    print("   - User personas: http://localhost:8000/api/users/{id}/persona/")
    print("   - Property personas: http://localhost:8000/api/properties/{id}/persona/")
    print("   - Recommendations: http://localhost:8000/api/users/{id}/recommendations/")
    print()
    print("For documentation on the LLM integration, see the README.md file.")

if __name__ == "__main__":
    print_header("Claude API Integration Setup")
    print("This script will help you set up the Claude API integration for rentify.ai.")
    
    check_env_file()
    check_dependencies()
    create_cache_directory()
    test_result = test_claude_integration()
    
    if test_result:
        print_next_steps()
    else:
        print("\n⚠️  Claude API integration test failed")
        print("Please check your API key and ensure it's valid.")
        print("You can run this script again at any time to retry the setup.")
        print("\nIf you need help getting a Claude API key, visit:")
        print("https://www.anthropic.com/api") 