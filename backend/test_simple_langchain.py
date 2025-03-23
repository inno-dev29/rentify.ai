"""
Test script for the simplified LangChain recommendation agent.
This script demonstrates the conversational recommendation capabilities
with a more straightforward and reliable implementation.
"""

import os
import sys
import django
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath('.')))
django.setup()

# Check if CLAUDE_API_KEY is in environment
if os.environ.get('CLAUDE_API_KEY'):
    logger.info(f"Claude API key found: {os.environ.get('CLAUDE_API_KEY')[:2]}...{os.environ.get('CLAUDE_API_KEY')[-4:]}")
else:
    logger.warning("Claude API key not found in environment variables")

# Import the recommendation agent and user model
from llm_services.services.simple_langchain_agent import SimpleRecommendationAgent
from django.contrib.auth import get_user_model

User = get_user_model()

def pretty_print_dict(d, indent=2):
    """Print a dictionary with nice formatting."""
    print(json.dumps(d, indent=indent))

def test_initial_recommendations(agent, user_id):
    """Test generating initial recommendations."""
    logger.info(f"Generating initial recommendations for user {user_id}")
    
    try:
        # Generate recommendations
        recommendations = agent.generate_recommendations(user_id)
        
        # Print the results
        print("\n=== INITIAL RECOMMENDATIONS ===")
        print(f"Personalized Explanation: {recommendations['personalized_explanation']}")
        
        print("\nRecommended Properties:")
        for i, prop in enumerate(recommendations['properties'], 1):
            print(f"{i}. Property ID: {prop.get('property_id')}")
            print(f"   Highlights: {prop.get('highlights')}")
            print()
        
        print("Follow-up Questions:")
        for i, question in enumerate(recommendations['follow_up_questions'], 1):
            print(f"{i}. {question}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in test_initial_recommendations: {str(e)}")
        return None

def test_refined_recommendations(agent, user_id, query):
    """Test refining recommendations based on user input."""
    logger.info(f"Generating refined recommendations for user {user_id} with query: {query}")
    
    try:
        # Generate recommendations with query
        recommendations = agent.generate_recommendations(user_id, query)
        
        # Print the results
        print("\n=== REFINED RECOMMENDATIONS ===")
        print(f"Personalized Explanation: {recommendations['personalized_explanation']}")
        
        print("\nRecommended Properties:")
        for i, prop in enumerate(recommendations['properties'], 1):
            print(f"{i}. Property ID: {prop.get('property_id')}")
            print(f"   Highlights: {prop.get('highlights')}")
            print()
        
        print("Follow-up Questions:")
        for i, question in enumerate(recommendations['follow_up_questions'], 1):
            print(f"{i}. {question}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in test_refined_recommendations: {str(e)}")
        return None

def run_conversation_test(user_id=1):
    """Run a complete conversation test with the recommendation agent."""
    logger.info(f"Starting conversation test with user ID {user_id}")
    
    try:
        # Get or create a test user
        user = User.objects.get(id=user_id)
        logger.info(f"Using existing user: {user.username}")
    except User.DoesNotExist:
        logger.info("Test user not found, skipping user verification")
    
    # Create the recommendation agent
    agent = SimpleRecommendationAgent()
    
    # Test initial recommendations
    initial_recs = test_initial_recommendations(agent, user_id)
    if not initial_recs:
        logger.error("Initial recommendations test failed")
        return
    
    # Test refined recommendations with a query
    query = "I'm looking for a 2-bedroom place with a nice kitchen, preferably near downtown"
    refined_recs = test_refined_recommendations(agent, user_id, query)
    if not refined_recs:
        logger.error("Refined recommendations test failed")
        return
    
    logger.info("Conversation test completed successfully")

if __name__ == "__main__":
    logger.info("Starting simplified LangChain recommendation agent test")
    
    try:
        logger.info("Using user with ID 1 for testing")
        run_conversation_test(user_id=1)
    except Exception as e:
        logger.error(f"Error running conversation test: {str(e)}")
    
    logger.info("Test completed") 