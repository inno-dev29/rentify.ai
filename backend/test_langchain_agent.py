"""
Test script for the LangChain recommendation agent.
This script demonstrates the conversational recommendation capabilities
with the ability to maintain context and use tools for more informed recommendations.
"""

import os
import sys
import django
import json
import logging

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rental_platform.settings")
django.setup()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the recommendation agent
from llm_services.services.langchain_agent import get_recommendation_agent
from users.models import User


def pretty_print_dict(d, indent=0):
    """Pretty print a dictionary."""
    for key, value in d.items():
        if isinstance(value, dict):
            print(" " * indent + str(key) + ":")
            pretty_print_dict(value, indent + 4)
        elif isinstance(value, list):
            print(" " * indent + str(key) + ":")
            for item in value:
                if isinstance(item, dict):
                    pretty_print_dict(item, indent + 4)
                    print()  # Add a newline between items
                else:
                    print(" " * (indent + 4) + str(item))
        else:
            print(" " * indent + str(key) + ": " + str(value))


def test_initial_recommendations(agent, user_id):
    """Test initial property recommendations."""
    logger.info(f"Generating initial recommendations for user {user_id}")
    
    # Generate recommendations
    recommendations = agent.generate_recommendations(user_id)
    
    # Print results
    print("\n== INITIAL RECOMMENDATIONS ==")
    print(f"Personalized Explanation: {recommendations.get('personalized_explanation', '')}")
    print("\nProperties:")
    
    for prop in recommendations.get('properties', []):
        print(f"\nProperty ID: {prop.get('property_id')}")
        print(f"Matching Score: {prop.get('matching_score')}/100")
        print("Strengths:")
        for strength in prop.get('strengths', []):
            print(f"  - {strength}")
        print("Weaknesses:")
        for weakness in prop.get('weaknesses', []):
            print(f"  - {weakness}")
        print(f"Reasoning: {prop.get('reasoning', '')}")
    
    print("\nFollow-up Questions:")
    for question in recommendations.get('follow_up_questions', []):
        print(f"  - {question}")
    
    return recommendations


def test_refined_recommendations(agent, user_id, feedback):
    """Test refined property recommendations based on feedback."""
    logger.info(f"Refining recommendations for user {user_id} with feedback: {feedback}")
    
    # Refine recommendations
    refined_recommendations = agent.refine_recommendations(user_id, feedback)
    
    # Print results
    print("\n== REFINED RECOMMENDATIONS ==")
    print(f"Personalized Explanation: {refined_recommendations.get('personalized_explanation', '')}")
    print("\nProperties:")
    
    for prop in refined_recommendations.get('properties', []):
        print(f"\nProperty ID: {prop.get('property_id')}")
        print(f"Matching Score: {prop.get('matching_score')}/100")
        print("Strengths:")
        for strength in prop.get('strengths', []):
            print(f"  - {strength}")
        print("Weaknesses:")
        for weakness in prop.get('weaknesses', []):
            print(f"  - {weakness}")
        print(f"Reasoning: {prop.get('reasoning', '')}")
    
    print("\nFollow-up Questions:")
    for question in refined_recommendations.get('follow_up_questions', []):
        print(f"  - {question}")
    
    return refined_recommendations


def run_conversation_test():
    """Run a simulated conversation to test the recommendation agent."""
    # Get the first user from the database
    try:
        user = User.objects.first()
        if not user:
            logger.error("No users found in the database. Please create a user first.")
            return
        
        user_id = user.id
        logger.info(f"Using user with ID {user_id} for testing")
        
        # Get recommendation agent
        agent = get_recommendation_agent()
        
        # Test initial recommendations
        initial_recommendations = test_initial_recommendations(agent, user_id)
        
        # Test refined recommendations with follow-up questions
        feedbacks = [
            "I'm looking for a property with a pool",
            "I need a place that allows pets",
            "What about properties closer to downtown?",
            "I'm looking for a property with at least 3 bedrooms"
        ]
        
        for feedback in feedbacks:
            input("Press Enter to continue with next feedback...")
            refined_recommendations = test_refined_recommendations(agent, user_id, feedback)
        
        # Clear conversation history
        agent.clear_conversation_history()
        logger.info("Conversation history cleared")
        
    except Exception as e:
        logger.error(f"Error running conversation test: {str(e)}")


if __name__ == "__main__":
    logger.info("Starting LangChain recommendation agent test")
    run_conversation_test()
    logger.info("Test completed") 