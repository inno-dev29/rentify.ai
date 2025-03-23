import os
import sys
import django
import json
import logging
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary models
from django.contrib.auth import get_user_model
User = get_user_model()

def test_conversational_recommendations_api():
    """Test the conversational recommendations API endpoint."""
    
    # Get admin user for testing
    try:
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            logger.warning("No admin user found for testing. Using first user.")
            admin_user = User.objects.first()
            
        logger.info(f"Using user: {admin_user.username}")
        
        # Get auth token for admin user
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=admin_user)
        logger.info(f"Using token: {token.key}")
        
        # Test endpoint
        base_url = "http://localhost:8005/api/llm/recommendations/conversational/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {token.key}"
        }
        
        # Test GET request
        logger.info("Testing GET request...")
        response = requests.get(base_url, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("GET request successful!")
            try:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                logger.error(f"Response is not valid JSON: {response.text}")
        else:
            logger.error(f"GET request failed: {response.text}")
        
        # Test POST request with feedback
        logger.info("Testing POST request with feedback...")
        payload = {"feedback": "I'm looking for a property with a nice view."}
        response = requests.post(base_url, headers=headers, json=payload)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("POST request successful!")
            try:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                logger.error(f"Response is not valid JSON: {response.text}")
        else:
            logger.error(f"POST request failed: {response.text}")
            
        # Test DELETE request to clear history
        logger.info("Testing DELETE request to clear history...")
        response = requests.delete(base_url, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("DELETE request successful!")
            try:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                logger.error(f"Response is not valid JSON: {response.text}")
        else:
            logger.error(f"DELETE request failed: {response.text}")
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        
if __name__ == "__main__":
    test_conversational_recommendations_api() 