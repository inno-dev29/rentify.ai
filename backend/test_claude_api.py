#!/usr/bin/env python
import os
import requests
import json

# Get the API key from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
api_key = None

if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('CLAUDE_API_KEY=') and '=' in line and line.strip().split('=', 1)[1].strip():
                api_key = line.strip().split('=', 1)[1].strip("'\"")
                break

if not api_key:
    print("ERROR: CLAUDE_API_KEY not found in .env file")
    exit(1)

# Claude API configuration
BASE_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-3-sonnet-20240229"
HEADERS = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

# Test payload
payload = {
    "model": MODEL,
    "system": "You are a helpful assistant.",
    "messages": [
        {"role": "user", "content": "Hello, can you generate a short test response to check if API is working?"}
    ],
    "max_tokens": 100,
    "temperature": 0.7
}

print(f"Testing Claude API with model: {MODEL}")
print(f"API key: {api_key[:5]}...{api_key[-5:]}")
print()

try:
    print("Sending request to Claude API...")
    response = requests.post(
        BASE_URL,
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\nAPI RESPONSE SUCCESS:")
        print(f"Content: {result['content'][0]['text']}")
        print(f"Model: {result.get('model', MODEL)}")
        if 'usage' in result:
            print(f"Tokens: input={result['usage'].get('input_tokens', 0)}, output={result['usage'].get('output_tokens', 0)}")
        print("\nAPI is working correctly!")
    else:
        print("\nAPI ERROR:")
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
except Exception as e:
    print(f"\nEXCEPTION: {str(e)}")

print("\nTest completed.") 