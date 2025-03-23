# LangChain Integration

This document explains how LangChain is integrated into rentify.ai to provide personalized property recommendations.

## Overview

rentify.ai uses LangChain to power a conversational recommendation system that helps users find properties matching their preferences. The system leverages Claude 3 Sonnet via the Anthropic API to generate personalized property recommendations based on user data and specific requirements.

## Components

### SimpleRecommendationAgent

The core of the recommendation system is the `SimpleRecommendationAgent` class, located in `llm_services/services/simple_langchain_agent.py`. This agent:

1. Fetches user data including preferences and profile information
2. Retrieves property data from the database
3. Uses LangChain's ChatAnthropic to generate personalized recommendations
4. Returns structured property recommendations with explanations and follow-up questions

### Key Features

- **Personalized Explanations**: Explains why specific properties match a user's preferences
- **Property Highlights**: Identifies key features of properties that align with user needs
- **Follow-up Questions**: Suggests questions to refine recommendations further
- **Queryable Interface**: Allows users to specify additional requirements through natural language

## Usage

### API Endpoint

The recommendation system is exposed through the `/api/recommendations/conversational/` endpoint. This endpoint:

- Requires authentication
- Accepts optional query parameters to refine recommendations
- Returns structured JSON with personalized recommendations

### Example Response

```json
{
  "personalized_explanation": "Based on your preference for being close to nature, I've recommended properties that offer immersive natural experiences...",
  "properties": [
    {
      "property_id": 8,
      "highlights": "Surrounded by protected desert, with an observatory for stargazing. Direct access to hiking trails."
    },
    {
      "property_id": 4,
      "highlights": "Eco-friendly treehouse retreat elevated 30 feet in an ancient forest. Panoramic views of nature."
    }
  ],
  "follow_up_questions": [
    "Are you looking for a more remote or populated area?",
    "Do you have a preference for warm/desert or cool/forested environments?"
  ]
}
```

## Technical Implementation

### LangChain Components Used

- **ChatAnthropic**: Provides access to Claude 3 Sonnet model
- **SystemMessage/HumanMessage**: Structures prompts for the LLM
- **JSON Output Parsing**: Ensures structured, consistent responses

### Environment Variables

The following environment variables are required:

- `CLAUDE_API_KEY`: API key for Anthropic's Claude service

## Testing

A test script is provided in `test_simple_langchain.py` that demonstrates:

1. Initial recommendations based on user profile
2. Refined recommendations based on specific queries
3. Response parsing and formatting

## Future Improvements

Potential enhancements to the recommendation system:

- **Conversation Memory**: Store and use conversation history for better context
- **User Preference Learning**: Improve recommendations over time based on user feedback
- **Multi-modal Recommendations**: Include image analysis for better property matching
- **Integration with Search**: Combine with traditional search for hybrid recommendations 