# LLM Services for rentify.ai

This package provides LLM integration for rentify.ai using DeepSeek and Claude APIs. It includes advanced caching capabilities, context management, and optimization features to reduce costs and improve efficiency.

## Features

- **Multiple Provider Support**: Integrates both DeepSeek and Claude LLMs
- **Optimized DeepSeek Client**: Enhanced version with better caching and context management
- **Unified Interface**: Single API for interacting with either provider
- **Response Caching**: File-based cache system that significantly reduces API costs
- **Conversation Context**: Maintains conversation history for better continuity
- **Embeddings Support**: Generate text embeddings for semantic search
- **Streaming Responses**: Real-time streaming for improved user experience
- **Server-side Caching**: Leverages DeepSeek's server-side caching capabilities
- **Debug Mode**: Mock responses for development without API calls
- **Cache Management**: Tools for monitoring and managing the cache

## Architecture

```
llm_services/
├── services/
│   ├── llm_client.py      # Base implementation with standard clients
│   ├── optimized_deepseek.py  # Optimized DeepSeek client
│   ├── llm_manager.py     # Manager for coordinating LLM clients
│   ├── cache.py           # File-based caching system
│   └── utils.py           # Common utility functions
├── views.py               # API endpoints for LLM features
├── management/
│   └── commands/          # Django management commands
└── models.py              # Django models for tracking usage
```

## Configuration

The following environment variables can be set in `.env` to configure the service:

```
# LLM API Keys
DEEPSEEK_API_KEY=your_deepseek_api_key
CLAUDE_API_KEY=your_claude_api_key

# Provider Settings
DEFAULT_LLM_PROVIDER=deepseek  # or 'claude'
DEBUG_LLM=False  # Set to True for mock responses

# Cache Settings
LLM_CACHE_DIR=.llm_cache
LLM_CACHE_TTL=604800  # 7 days in seconds

# DeepSeek Optimization Settings
USE_OPTIMIZED_DEEPSEEK=True
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_CONTEXT_WINDOW=16000
DEEPSEEK_ENABLE_SERVER_CACHE=True
DEEPSEEK_EMBEDDING_MODEL=deepseek-embedding
```

## Usage Examples

### Basic Usage

```python
from llm_services.services.llm_manager import llm_manager

# Generate a response using the default provider
response = llm_manager.generate_response(
    system_prompt="You are a helpful assistant.",
    user_prompt="What's the weather like today?",
    temperature=0.7
)

print(response["content"])
```

### Conversation Context

```python
from llm_services.services.llm_manager import llm_manager

# Generate responses in a conversation
context_id = "user_conversation_123"

# First message
response1 = llm_manager.generate_response(
    system_prompt="You are a helpful assistant.",
    user_prompt="Hi there! Can you help me find a rental property?",
    context_id=context_id
)

# Second message (maintains conversation history)
response2 = llm_manager.generate_response(
    system_prompt="You are a helpful assistant.",
    user_prompt="I'm looking for something in Paris with 2 bedrooms.",
    context_id=context_id
)

# Clear context when conversation is done
llm_manager.clear_conversation_context(context_id)
```

### Embeddings

```python
from llm_services.services.llm_manager import llm_manager

# Generate embeddings for semantic search
texts = [
    "Luxury apartment with ocean view",
    "Cozy cabin in the mountains",
    "Downtown loft with city views"
]

embeddings = llm_manager.create_embeddings(texts)
```

## Cache Management

The cache can be managed using the `manage_llm_cache.py` script:

```bash
# Show cache statistics
python manage_llm_cache.py stats

# Clear all cache entries
python manage_llm_cache.py clear

# Clear entries older than 7 days
python manage_llm_cache.py clear --days 7

# List all cache entries
python manage_llm_cache.py list

# List all conversation contexts
python manage_llm_cache.py contexts list

# Clear a specific context
python manage_llm_cache.py contexts clear <context_id>

# Clear all contexts
python manage_llm_cache.py contexts clear --all

# Optimize the cache (remove corrupted entries, etc.)
python manage_llm_cache.py optimize
```

## Testing

Two test scripts are provided to verify the LLM integration:

1. `test_llm.py` - Tests the standard LLM clients
2. `test_optimized_deepseek.py` - Tests the optimized DeepSeek client

Run them with:

```bash
# Test standard clients
python test_llm.py

# Test optimized DeepSeek client
python test_optimized_deepseek.py

# Run in debug mode (no API calls)
DEBUG_LLM=True python test_optimized_deepseek.py
```

## Performance Optimization

The optimized DeepSeek client implements several performance enhancements:

1. **Context-aware Caching**: Cache responses based on the full conversation context
2. **Server-side Caching**: Use DeepSeek's `cache_id` for server-side caching
3. **Streaming Responses**: Receive responses token by token for a more responsive UI
4. **Response Chunking**: Split long prompts into chunks to optimize token usage
5. **Automatic Retries**: Exponential backoff for API failures

## Cost Optimization

To optimize costs:

1. Use a low temperature (0-0.2) for deterministic responses, which enables caching
2. Leverage context windows to reduce token usage across multiple queries
3. Run `manage_llm_cache.py optimize` periodically to clean up the cache
4. Monitor usage with the cache statistics feature

## License

This package is part of rentify.ai and is subject to the same license terms. 