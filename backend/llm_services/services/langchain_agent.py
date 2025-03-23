"""
Enhanced recommendation system using LangChain.
Provides a conversational recommendation agent with advanced reasoning capabilities.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from langchain_community.llms import Anthropic
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.chains import LLMChain, SequentialChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, Tool
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.tools.render import format_tool_to_openai_function

from django.conf import settings
from properties.models import Property
from reviews.models import Review
from users.models import User

# Setup logging
logger = logging.getLogger(__name__)

# Pydantic models for structured outputs
class PropertyAnalysis(BaseModel):
    """Analysis of a property's strengths and weaknesses."""
    property_id: int = Field(description="The ID of the property")
    strengths: List[str] = Field(description="List of property strengths")
    weaknesses: List[str] = Field(description="List of property weaknesses")
    matching_score: int = Field(description="Score from 1-100 of how well the property matches the user's preferences")
    reasoning: str = Field(description="Detailed reasoning for the matching score")

class RecommendationOutput(BaseModel):
    """Structured recommendation results."""
    properties: List[PropertyAnalysis] = Field(description="List of analyzed properties")
    personalized_explanation: str = Field(description="Personalized explanation of the recommendations")
    follow_up_questions: List[str] = Field(description="Potential follow-up questions to refine recommendations")

# Tools for the recommendation agent
class PropertyDataRetriever:
    """Tool for retrieving property data."""
    
    def __init__(self):
        self.name = "property_data_retriever"
        self.description = "Retrieves detailed property data including amenities, location, price, and reviews"
    
    def _get_property_data(self, property_id: int) -> Dict:
        """Get detailed data for a specific property."""
        try:
            property_obj = Property.objects.get(id=property_id)
            
            # Get property reviews
            reviews = Review.objects.filter(booking__property=property_obj)
            review_data = []
            for review in reviews:
                review_data.append({
                    "rating": review.rating,
                    "comment": review.comment,
                    "date": review.created_at.strftime("%Y-%m-%d")
                })
            
            # Format full property data
            property_data = {
                "id": property_obj.id,
                "title": property_obj.title,
                "description": property_obj.description,
                "location": {
                    "address": property_obj.address,
                    "city": property_obj.city,
                    "state": property_obj.state,
                    "country": property_obj.country,
                    "zip_code": property_obj.zip_code,
                },
                "details": {
                    "property_type": property_obj.property_type,
                    "bedrooms": property_obj.bedroom_count,
                    "bathrooms": property_obj.bathroom_count,
                    "max_guests": property_obj.max_guests,
                    "size_sqm": property_obj.size_sqm,
                },
                "pricing": {
                    "base_price": float(property_obj.base_price),
                    "cleaning_fee": float(property_obj.cleaning_fee),
                    "has_discount": property_obj.has_discount,
                    "discount_percentage": property_obj.discount_percentage,
                },
                "amenities": [amenity.name for amenity in property_obj.amenities.all()],
                "reviews": review_data,
                "average_rating": property_obj.average_rating,
                "review_count": reviews.count(),
            }
            
            return property_data
            
        except Property.DoesNotExist:
            return {"error": f"Property with ID {property_id} not found"}
        except Exception as e:
            logger.error(f"Error retrieving property data: {str(e)}")
            return {"error": f"Error retrieving property data: {str(e)}"}
    
    def __call__(self, property_id: int) -> str:
        """Execute the tool with the given property ID."""
        try:
            property_id = int(property_id)
            property_data = self._get_property_data(property_id)
            return json.dumps(property_data, indent=2)
        except ValueError:
            return json.dumps({"error": "Invalid property ID. Must be an integer."})

class UserPreferenceRetriever:
    """Tool for retrieving user preferences."""
    
    def __init__(self):
        self.name = "user_preference_retriever"
        self.description = "Retrieves user preferences, booking history, and saved properties"
    
    def _get_user_preferences(self, user_id: int) -> Dict:
        """Get preferences and history for a specific user."""
        try:
            user = User.objects.get(id=user_id)
            
            # Get booking history
            bookings = user.bookings.all().order_by('-created_at')[:5]
            booking_history = []
            for booking in bookings:
                booking_history.append({
                    "property_id": booking.property.id,
                    "property_title": booking.property.title,
                    "start_date": booking.start_date.strftime("%Y-%m-%d"),
                    "end_date": booking.end_date.strftime("%Y-%m-%d"),
                    "property_type": booking.property.property_type,
                    "total_price": float(booking.total_price),
                })
            
            # Get saved properties
            saved_properties = user.saved_properties.all()
            saved_property_data = []
            for prop in saved_properties:
                saved_property_data.append({
                    "id": prop.id,
                    "title": prop.title,
                    "property_type": prop.property_type,
                    "bedrooms": prop.bedroom_count,
                    "bathrooms": prop.bathroom_count,
                    "base_price": float(prop.base_price),
                })
            
            # Format user preferences
            preferences = {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "account_age_days": (user.last_login - user.date_joined).days if user.last_login else 0,
                "booking_history": booking_history,
                "saved_properties": saved_property_data,
                "preferred_property_types": user.preferred_property_types if hasattr(user, 'preferred_property_types') else [],
                "preferred_amenities": user.preferred_amenities if hasattr(user, 'preferred_amenities') else [],
                "budget_range": {
                    "min": float(user.min_budget) if hasattr(user, 'min_budget') and user.min_budget else 0,
                    "max": float(user.max_budget) if hasattr(user, 'max_budget') and user.max_budget else 9999,
                },
            }
            
            return preferences
            
        except User.DoesNotExist:
            return {"error": f"User with ID {user_id} not found"}
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return {"error": f"Error retrieving user preferences: {str(e)}"}
    
    def __call__(self, user_id: int) -> str:
        """Execute the tool with the given user ID."""
        try:
            user_id = int(user_id)
            user_data = self._get_user_preferences(user_id)
            return json.dumps(user_data, indent=2)
        except ValueError:
            return json.dumps({"error": "Invalid user ID. Must be an integer."})

class SimilarPropertyFinder:
    """Tool for finding properties similar to a specified property."""
    
    def __init__(self):
        self.name = "similar_property_finder"
        self.description = "Finds properties similar to a specified property based on type, price range, and amenities"
    
    def _find_similar_properties(self, property_id: int, limit: int = 5) -> List[Dict]:
        """Find properties similar to the specified property."""
        try:
            # Get the reference property
            reference_property = Property.objects.get(id=property_id)
            
            # Define similarity criteria
            property_type = reference_property.property_type
            price_min = float(reference_property.base_price) * 0.7  # 30% lower
            price_max = float(reference_property.base_price) * 1.3  # 30% higher
            bedrooms = reference_property.bedroom_count
            reference_amenities = set(reference_property.amenities.all().values_list('id', flat=True))
            
            # Find similar properties
            similar_properties = Property.objects.filter(
                property_type=property_type,
                base_price__gte=price_min,
                base_price__lte=price_max,
                bedroom_count__gte=bedrooms-1,
                bedroom_count__lte=bedrooms+1
            ).exclude(id=property_id)
            
            # Sort by amenity similarity
            result = []
            for property_obj in similar_properties:
                property_amenities = set(property_obj.amenities.all().values_list('id', flat=True))
                amenity_overlap = len(reference_amenities.intersection(property_amenities))
                
                result.append({
                    "id": property_obj.id,
                    "title": property_obj.title,
                    "property_type": property_obj.property_type,
                    "bedrooms": property_obj.bedroom_count,
                    "bathrooms": property_obj.bathroom_count,
                    "base_price": float(property_obj.base_price),
                    "amenity_overlap": amenity_overlap,
                    "city": property_obj.city,
                    "average_rating": property_obj.average_rating,
                })
            
            # Sort by amenity overlap (descending)
            result.sort(key=lambda x: x['amenity_overlap'], reverse=True)
            
            return result[:limit]
            
        except Property.DoesNotExist:
            return [{"error": f"Property with ID {property_id} not found"}]
        except Exception as e:
            logger.error(f"Error finding similar properties: {str(e)}")
            return [{"error": f"Error finding similar properties: {str(e)}"}]
    
    def __call__(self, args: str) -> str:
        """Execute the tool with the given property ID and optional limit."""
        try:
            # Parse arguments
            args_dict = json.loads(args)
            property_id = int(args_dict.get("property_id"))
            limit = int(args_dict.get("limit", 5))
            
            similar_properties = self._find_similar_properties(property_id, limit)
            return json.dumps(similar_properties, indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid argument format. Expected JSON string with 'property_id' and optional 'limit'."})
        except ValueError:
            return json.dumps({"error": "Invalid property ID or limit. Both must be integers."})
        except Exception as e:
            return json.dumps({"error": f"Error: {str(e)}"})

# Create a LangChain-powered recommendation agent
class LangChainRecommendationAgent:
    """
    Advanced recommendation agent powered by LangChain.
    Uses tools, memory, and structured output to generate high-quality recommendations.
    """
    
    def __init__(self):
        """Initialize the LangChain recommendation agent."""
        self.anthropic_api_key = settings.CLAUDE_API_KEY
        self.model_name = "claude-3-sonnet-20240229"
        
        # Initialize the LLM
        self.llm = Anthropic(
            anthropic_api_key=self.anthropic_api_key,
            model=self.model_name,
            temperature=0.7,
            max_tokens=4000
        )
        
        # Initialize tools
        self.tools = [
            Tool(
                name="property_data_retriever",
                func=PropertyDataRetriever(),
                description="Retrieves detailed property data including amenities, location, price, and reviews. Input should be a property ID (integer)."
            ),
            Tool(
                name="user_preference_retriever",
                func=UserPreferenceRetriever(),
                description="Retrieves user preferences, booking history, and saved properties. Input should be a user ID (integer)."
            ),
            Tool(
                name="similar_property_finder",
                func=SimilarPropertyFinder(),
                description="""Finds properties similar to a specified property. 
                Input should be a JSON string with 'property_id' (required) and 'limit' (optional, default 5).
                Example: {"property_id": 123, "limit": 3}"""
            )
        ]
        
        # Initialize agent with memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define system prompt for the agent
        system_prompt = """You are an advanced property recommendation assistant for a rental platform.
        Your goal is to help users find the perfect property for their needs by providing personalized recommendations.
        
        Use the available tools to:
        1. Retrieve detailed property information
        2. Understand user preferences from their profile and history
        3. Find similar properties based on preferences
        
        When analyzing properties, consider:
        - How well the property matches the user's explicit preferences
        - Implicit preferences based on their browsing and booking history
        - The quality of reviews and overall rating
        - Value for money compared to similar properties
        
        Provide thoughtful analysis for each recommended property, explaining why it's a good match.
        Always include strengths and potential drawbacks of each property for balanced recommendations.
        
        Your final recommendation should be structured and easy to understand, with:
        - A personalized explanation of why these properties were selected
        - Analysis of each property's match to the user's needs
        - Suggestions for follow-up questions to refine recommendations
        
        Be conversational but efficient, and maintain context throughout the conversation.
        """
        
        # Create a custom ReAct agent that works with Anthropic
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Convert tools to OpenAI functions
        llm_with_tools = self.llm.bind(
            functions=[format_tool_to_openai_function(t) for t in self.tools]
        )
        
        # Create the agent
        self.agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", []),
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x.get("intermediate_steps", [])
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )
        
        # Output parser for structured recommendations
        self.parser = PydanticOutputParser(pydantic_object=RecommendationOutput)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
    
    def generate_recommendations(self, user_id: int, query: Optional[str] = None) -> Dict:
        """
        Generate property recommendations for a user with optional query refinement.
        
        Args:
            user_id: The ID of the user to generate recommendations for
            query: Optional natural language query to refine recommendations
            
        Returns:
            Structured recommendations in dictionary format
        """
        try:
            # Set up the user query
            if query:
                user_input = f"Generate property recommendations for user {user_id} with these preferences: {query}"
            else:
                user_input = f"Generate property recommendations for user {user_id} based on their profile and history"
            
            # Run the agent to get recommendations
            agent_response = self.agent_executor.invoke({"input": user_input})
            
            # Format the output for structured parsing
            format_prompt = PromptTemplate(
                template="""
                Based on the following recommendation information, create a structured output that follows the exact format below:
                
                {format_instructions}
                
                Recommendation information:
                {agent_output}
                
                Structured Output:
                """,
                input_variables=["agent_output"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )
            
            format_chain = LLMChain(llm=self.llm, prompt=format_prompt)
            formatted_output = format_chain.run(agent_output=agent_response["output"])
            
            # Parse and fix the output if needed
            try:
                structured_output = self.parser.parse(formatted_output)
                return structured_output.dict()
            except Exception as parsing_error:
                logger.warning(f"Error parsing output, attempting to fix: {str(parsing_error)}")
                fixed_output = self.fixing_parser.parse(formatted_output)
                return fixed_output.dict()
                
        except Exception as e:
            logger.error(f"Error generating recommendations with LangChain: {str(e)}")
            return {
                "error": f"Failed to generate recommendations: {str(e)}",
                "properties": [],
                "personalized_explanation": "We encountered an error while processing your request.",
                "follow_up_questions": ["Would you like to try again?"]
            }
    
    def refine_recommendations(self, user_id: int, feedback: str) -> Dict:
        """
        Refine recommendations based on user feedback.
        
        Args:
            user_id: The ID of the user to refine recommendations for
            feedback: User feedback or follow-up question
            
        Returns:
            Refined recommendations in dictionary format
        """
        try:
            # Run the agent with the feedback
            agent_response = self.agent_executor.invoke({"input": feedback})
            
            # Format and parse the output
            format_prompt = PromptTemplate(
                template="""
                Based on the following refined recommendation information, create a structured output that follows the exact format below:
                
                {format_instructions}
                
                Refined recommendation information:
                {agent_output}
                
                Structured Output:
                """,
                input_variables=["agent_output"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )
            
            format_chain = LLMChain(llm=self.llm, prompt=format_prompt)
            formatted_output = format_chain.run(agent_output=agent_response["output"])
            
            # Parse and fix the output if needed
            try:
                structured_output = self.parser.parse(formatted_output)
                return structured_output.dict()
            except Exception as parsing_error:
                logger.warning(f"Error parsing refined output, attempting to fix: {str(parsing_error)}")
                fixed_output = self.fixing_parser.parse(formatted_output)
                return fixed_output.dict()
                
        except Exception as e:
            logger.error(f"Error refining recommendations with LangChain: {str(e)}")
            return {
                "error": f"Failed to refine recommendations: {str(e)}",
                "properties": [],
                "personalized_explanation": "We encountered an error while processing your feedback.",
                "follow_up_questions": ["Would you like to try a different approach?"]
            }
    
    def clear_conversation_history(self):
        """Clear the conversation history/memory."""
        self.memory.clear()

# Function to create a singleton instance
_agent_instance = None

def get_recommendation_agent():
    """Get or create the recommendation agent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LangChainRecommendationAgent()
    return _agent_instance 