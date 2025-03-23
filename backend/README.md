## LLM Services

### Conversational Recommendations API

The LangChain-powered conversational recommendations API provides a natural language interface for users to get personalized property recommendations and refine them through conversation.

#### Endpoints

- `GET /api/llm/recommendations/conversational/` - Get initial recommendations
- `POST /api/llm/recommendations/conversational/` - Refine recommendations with user feedback
- `DELETE /api/llm/recommendations/conversational/` - Clear conversation history

#### Testing the API

To test the conversational recommendations API:

1. Make sure the backend server is running on port 8005:
```
cd backend
source venv/bin/activate
python manage.py runserver 8005
```

2. Run the test script:
```
cd backend
source venv/bin/activate
python test_conversational_api.py
```

This will perform GET, POST, and DELETE requests to the API endpoint and print the results.

#### Frontend Integration

The frontend application integrates with the API through the `llmService.ts` service. The `ConversationalRecommendations` component provides a user-friendly interface for interacting with the recommendations.

To access the conversational recommendations UI, navigate to `/recommendations/conversational` in the frontend application.

### Troubleshooting

If you encounter any issues with the API:

1. Check that the Django server is running on port 8005
2. Verify that the CLAUDE_API_KEY is set in the environment variables
3. Ensure that the LangChain dependencies are installed correctly:
```
pip install -r requirements.txt
```

4. Check for import errors in `simple_langchain_agent.py` - LangChain's API has been changing rapidly, so imports may need to be updated 