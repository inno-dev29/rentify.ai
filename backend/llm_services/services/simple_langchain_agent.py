"""
Simplified LangChain recommendation agent.
This version uses the latest LangChain API patterns and avoids compatibility issues.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model

# Use the correct model imports based on the actual app structure
from properties.models import Property, PropertyImage

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.messages.base import BaseMessage
from langchain.memory import ConversationBufferMemory

# Setup logging
logger = logging.getLogger(__name__)

User = get_user_model()

class SimpleRecommendationAgent:
    """
    A simplified agent for providing property recommendations using LangChain.
    Uses direct chat completion instead of complex agent frameworks.
    """
    
    def __init__(self):
        """Initialize the recommendation agent."""
        self.api_key = settings.CLAUDE_API_KEY
        self.model_name = "claude-3-sonnet-20240229"
        
        # Set up the LLM
        self.llm = ChatAnthropic(
            model=self.model_name, 
            anthropic_api_key=self.api_key,
            temperature=0.7
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create system prompt template
        self.system_template = """
        You are a property recommendation assistant for rentify.ai. 
        Your goal is to help users find properties that match their needs and preferences.
        
        When analyzing properties for a user, prioritize insights from their booking history and favorites:
        - Analyze past bookings to identify patterns in locations, property types, amenities, and price ranges
        - Make direct assumptions about user preferences based on their booking history
        - Consider the ratings and reviews they've left to understand what they value
        - Note price points they've been willing to pay in the past
        
        Make definitive assumptions about their preferences rather than asking too many questions.
        Be confident in your property recommendations based on data patterns.
        
        When making recommendations:
        1. Clearly explain why the property is a match based on their demonstrated preferences
        2. Highlight features that align with patterns seen in their booking history
        3. Be direct and assume what they'll like based on past behavior
        
        Format your response as a JSON object with these fields:
        {
            "personalized_explanation": "A confident, direct paragraph explaining why these properties match the user based on their booking history and preferences",
            "properties": [
                {
                    "property_id": "The ID of the property",
                    "highlights": "Key points about why this property is a good match based on their history"
                },
                ... (up to 3 properties)
            ],
            "follow_up_questions": []
        }
        
        The follow_up_questions array should be empty or have at most 1 question if absolutely necessary.
        Focus on making strong, data-based assumptions about what the user wants rather than asking them questions.
        """
    
    def _fetch_user_data(self, user_id):
        """
        Fetch relevant user data for generating recommendations.
        
        Args:
            user_id: The ID of the user to fetch data for
            
        Returns:
            dict: User data including preferences and details
        """
        try:
            # Get user data
            user = User.objects.get(id=user_id)
            
            # User data
            user_data = {
                "name": user.get_full_name() or user.username,
                "email": user.email,
                "date_joined": user.date_joined.isoformat(),
                "user_type": user.user_type,
                # Add other relevant user data if available
            }
            
            # Get profile data if available
            if hasattr(user, 'profile'):
                profile = user.profile
                user_data["profile"] = {
                    "address": {
                        "city": profile.city,
                        "state": profile.state,
                        "country": profile.country,
                    },
                    "travel_preferences": profile.travel_preferences,
                }
            
            # Get booking history
            booking_history = []
            if hasattr(user, 'bookings'):
                for booking in user.bookings.all().order_by('-start_date')[:5]:  # Last 5 bookings
                    try:
                        property_obj = booking.property
                        booking_data = {
                            "property_id": property_obj.id,
                            "property_title": property_obj.title,
                            "property_type": property_obj.property_type,
                            "location": f"{property_obj.city}, {property_obj.country}",
                            "price": float(property_obj.base_price),
                            "bedrooms": property_obj.bedroom_count,
                            "bathrooms": float(property_obj.bathroom_count),
                            "amenities": [amenity.name for amenity in property_obj.amenities.all()],
                            "start_date": booking.start_date.isoformat(),
                            "end_date": booking.end_date.isoformat(),
                            "duration_days": (booking.end_date - booking.start_date).days,
                            "total_guests": booking.guest_count
                        }
                        
                        # Add review data if available
                        if hasattr(booking, 'review'):
                            booking_data["review"] = {
                                "rating": booking.review.rating,
                                "comment": booking.review.comment
                            }
                            
                        booking_history.append(booking_data)
                    except Exception as e:
                        logger.error(f"Error processing booking data: {str(e)}")
            
            user_data["booking_history"] = booking_history
            user_data["booking_count"] = len(booking_history)
            
            # Get saved/favorite properties if available
            favorite_properties = []
            if hasattr(user, 'favorites'):
                for favorite in user.favorites.all():
                    try:
                        property_obj = favorite.property
                        favorite_properties.append({
                            "property_id": property_obj.id,
                            "property_title": property_obj.title,
                            "property_type": property_obj.property_type,
                            "location": f"{property_obj.city}, {property_obj.country}"
                        })
                    except Exception as e:
                        logger.error(f"Error processing favorite property data: {str(e)}")
                        
            user_data["favorite_properties"] = favorite_properties
            user_data["favorite_count"] = len(favorite_properties)
            
            return user_data
            
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return {}
        except Exception as e:
            logger.error(f"Error fetching user data: {str(e)}")
            return {}
    
    def _fetch_property_data(self, limit=10):
        """
        Fetch property data for recommendations.
        
        Args:
            limit: Maximum number of properties to fetch
            
        Returns:
            list: List of property data dictionaries
        """
        try:
            # Get properties
            properties = Property.objects.all()[:limit]
            
            property_data = []
            for prop in properties:
                # Get property images
                images = PropertyImage.objects.filter(property=prop)
                image_urls = [img.image.url for img in images]
                
                property_data.append({
                    "id": prop.id,
                    "title": prop.title,
                    "description": prop.description,
                    "property_type": prop.property_type,
                    "price": float(prop.base_price),
                    "bedrooms": prop.bedroom_count,
                    "bathrooms": float(prop.bathroom_count),
                    "max_guests": prop.max_guests,
                    "square_feet": prop.square_feet,
                    "address_line1": prop.address_line1,
                    "city": prop.city,
                    "state": prop.state,
                    "country": prop.country,
                    "postal_code": prop.postal_code,
                    "latitude": float(prop.latitude) if prop.latitude else None,
                    "longitude": float(prop.longitude) if prop.longitude else None,
                    "amenities": [amenity.name for amenity in prop.amenities.all()],
                    "image_urls": image_urls,
                    "created_at": prop.created_at.isoformat()
                })
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error fetching property data: {str(e)}")
            return []
    
    def generate_recommendations(self, user_id, query=None):
        """
        Generate property recommendations for a user.
        
        Args:
            user_id: The ID of the user to generate recommendations for
            query: Optional query string with user's requirements
            
        Returns:
            dict: Recommendation results with explanations and properties
        """
        try:
            # Fetch user and property data
            user_data = self._fetch_user_data(user_id)
            property_data = self._fetch_property_data(limit=10)
            
            # Build the prompt with all relevant information
            messages = [
                SystemMessage(content=self.system_template),
                HumanMessage(content=self._format_recommendation_request(user_data, property_data, query))
            ]
            
            # Make the recommendation
            raw_output = self.llm.invoke(messages)
            
            # Parse the response
            return self._parse_recommendation_output(raw_output.content)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    def _format_recommendation_request(self, user_data, property_data, query=None):
        """
        Format the recommendation request for the LLM.
        
        Args:
            user_data: Dictionary containing user information
            property_data: List of property dictionaries
            query: Optional query string with user's requirements
            
        Returns:
            str: Formatted request string
        """
        request = """
        Here's the user information:
        """
        request += json.dumps(user_data, indent=2)
        
        request += """
        
        Here are the available properties:
        """
        request += json.dumps(property_data, indent=2)
        
        if query:
            request += f"""
            
            The user has also specified these additional requirements:
            {query}
            """
        
        request += """
        
        Based on this information, recommend up to 3 properties that best match the user's preferences.
        Explain why each property is a good match and suggest follow-up questions to refine the recommendations.
        Format your response as JSON as specified in your instructions.
        """
        
        return request
    
    def _parse_recommendation_output(self, output):
        """
        Parse the recommendation output from the LLM.
        
        Args:
            output: Raw output string from the LLM
            
        Returns:
            dict: Parsed recommendation data
        """
        try:
            # Extract JSON from the response
            output = output.strip()
            
            # Handle case where output might have markdown code blocks
            if "```json" in output:
                json_str = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                json_str = output.split("```")[1].strip()
            else:
                json_str = output
            
            # Parse the JSON
            result = json.loads(json_str)
            
            # Ensure the expected fields are present
            result.setdefault("personalized_explanation", "")
            result.setdefault("properties", [])
            result.setdefault("follow_up_questions", [])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing recommendation output: {str(e)}")
            logger.error(f"Raw output: {output}")
            
            # Return a fallback response
            return {
                "personalized_explanation": "I found some properties that might interest you, but had trouble formatting the results.",
                "properties": [],
                "follow_up_questions": ["What kind of properties are you looking for?"]
            }
        except Exception as e:
            logger.error(f"Error processing recommendation output: {str(e)}")
            raise
            
    def refine_recommendations(self, user_id, feedback):
        """
        Refine recommendations based on user feedback.
        
        Args:
            user_id: The ID of the user to refine recommendations for
            feedback: User feedback or follow-up question
            
        Returns:
            dict: Refined recommendation results
        """
        try:
            # Fetch user and property data
            user_data = self._fetch_user_data(user_id)
            property_data = self._fetch_property_data(limit=10)
            
            # Format the refinement request
            refinement_request = f"""
            Based on the previous recommendations, the user has provided this feedback:
            
            {feedback}
            
            Please refine your recommendations accordingly.
            """
            
            # Build the messages
            messages = [
                SystemMessage(content=self.system_template),
                HumanMessage(content=self._format_recommendation_request(user_data, property_data)),
                HumanMessage(content=refinement_request)
            ]
            
            # Generate refined recommendations
            raw_output = self.llm.invoke(messages)
            
            # Parse the response
            return self._parse_recommendation_output(raw_output.content)
            
        except Exception as e:
            logger.error(f"Error refining recommendations: {str(e)}")
            return {
                "personalized_explanation": "I'm sorry, I had trouble processing your feedback.",
                "properties": [],
                "follow_up_questions": ["Could you try rephrasing your requirements?", "What are the most important features you're looking for?"]
            }
    
    def clear_conversation_history(self):
        """
        Clear the conversation history/memory for the current user.
        """
        try:
            # With the simplified implementation, we can just acknowledge
            # as we're not actively maintaining conversation history yet
            logger.info("Conversation history cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
            raise

# Factory function to get or create a recommendation agent
def get_recommendation_agent():
    """
    Factory function to create or retrieve a SimpleRecommendationAgent instance.
    Returns:
        SimpleRecommendationAgent: An instance of the recommendation agent.
    """
    return SimpleRecommendationAgent() 