# Advanced Recommendation System with LangChain

This document outlines the implementation and usage of the advanced property recommendation system powered by LangChain, which enhances the rental platform with conversational, context-aware recommendations.

## Overview

The LangChain-powered recommendation system provides significant enhancements over traditional recommendation approaches:

1. **Conversational Recommendations**: Maintains context throughout a conversation to provide increasingly relevant recommendations based on user feedback.

2. **Agent-based Architecture**: Uses specialized tools to fetch and analyze property data, user preferences, and find similar properties dynamically during the recommendation process.

3. **Transparent Reasoning**: Provides detailed explanations of why each property is recommended, including strengths, weaknesses, and a matching score with reasoning.

4. **Structured Output**: Returns consistently structured recommendations that are easy to process and display in the frontend.

5. **Follow-up Suggestions**: Suggests relevant follow-up questions to help users refine their search.

## Architecture

The recommendation system is built using the following components:

### LangChain Components

- **LLM Integration**: The system uses Claude's API through LangChain's Anthropic integration.
- **Agent Framework**: Uses LangChain's ReAct agent to enable reasoning and tool use.
- **Memory**: Maintains conversation history for contextual recommendations.
- **Tools**: Custom tools for retrieving property data, user preferences, and finding similar properties.
- **Output Parsers**: Ensures structured, consistent responses via Pydantic model validation.

### Tools

The agent has access to three specialized tools:

1. **PropertyDataRetriever**: Fetches detailed information about properties including amenities, pricing, and reviews.
2. **UserPreferenceRetriever**: Retrieves user preferences, booking history, and saved properties.
3. **SimilarPropertyFinder**: Finds properties similar to a specified property based on type, price, and amenities.

### Structured Output

Recommendations are returned in a consistent structure:

```json
{
  "properties": [
    {
      "property_id": 123,
      "strengths": ["Close to downtown", "Recently renovated", "Has a pool"],
      "weaknesses": ["No pets allowed", "Limited parking"],
      "matching_score": 85,
      "reasoning": "This property matches 85% of your preferences because..."
    },
    // Additional properties...
  ],
  "personalized_explanation": "Based on your preference for downtown locations with pools...",
  "follow_up_questions": [
    "Would you prefer a property that allows pets?",
    "Is a parking space important to you?"
  ]
}
```

## API Endpoints

### User Endpoints

- **GET /api/llm/me/conversational-recommendations/**
  - Generates initial recommendations for the current user
  - Optional query parameter: `query` for initial preferences

- **POST /api/llm/me/conversational-recommendations/**
  - Refines recommendations based on user feedback
  - Request body: `{"feedback": "I need a place that allows pets"}`

- **DELETE /api/llm/me/conversational-recommendations/**
  - Clears the conversation history/memory

### Admin Endpoints

- **GET /api/llm/admin/user/{user_id}/conversational-recommendations/**
  - Generates recommendations for a specific user (admin only)

- **POST /api/llm/admin/user/{user_id}/conversational-recommendations/**
  - Refines recommendations for a specific user based on admin feedback (admin only)

## Usage Examples

### Initial Recommendation Request

```http
GET /api/llm/me/conversational-recommendations/?query=I'm looking for a beachfront property
```

### Follow-up Refining Request

```http
POST /api/llm/me/conversational-recommendations/
Content-Type: application/json

{
  "feedback": "I need a place with at least 3 bedrooms and that allows pets"
}
```

## Implementation Details

The system is implemented as a singleton to maintain conversation state efficiently. Key components:

1. **LangChainRecommendationAgent**: Main class that coordinates the recommendation process.
2. **get_recommendation_agent()**: Function to get or create the agent singleton.
3. **Custom Tools**: Classes that encapsulate property data retrieval and analysis.
4. **API Views**: Django REST framework views that expose the functionality as API endpoints.

## Testing

A test script is provided (`test_langchain_agent.py`) to demonstrate the recommendation system's capabilities. Run it with:

```
python test_langchain_agent.py
```

## Benefits Over Traditional Approaches

1. **Context Awareness**: Unlike stateless recommendation systems, this maintains context throughout the conversation.
2. **Explanation Transparency**: Provides detailed reasoning for each recommendation.
3. **Dynamic Refinement**: Recommendations improve as users provide more information.
4. **Hybrid Approach**: Combines collaborative filtering (looking at similar users) with content-based recommendations.
5. **Adaptive Learning**: The agent can adapt to changing preferences within a session.

## Future Enhancements

1. **User-specific Memory**: Store conversation history per user instead of using a global singleton.
2. **Feedback Integration**: Use recommendation feedback to improve future recommendations.
3. **Multi-step Reasoning**: Implement more complex reasoning chains for specialized recommendation types.
4. **Integration with Vector Database**: Store property embeddings for faster similarity search.
5. **A/B Testing Framework**: Compare different recommendation strategies. 