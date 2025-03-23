"""
Optimized DeepSeek LLM client integration for the rental platform.
Implements advanced caching strategies and performance optimizations.
"""

import json
import logging
import os
import requests
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from django.conf import settings
from .llm_client import BaseLLMClient
from .cache import llm_cache
from .cache_analyzer import track_deepseek_server_cache

# Setup logging
logger = logging.getLogger(__name__)

class OptimizedDeepSeekClient(BaseLLMClient):
    """
    Optimized client for DeepSeek LLM with advanced caching features.
    
    Improvements over the base implementation:
    1. Uses latest DeepSeek model (v2.5)
    2. Implements context-aware caching
    3. Supports server-side response caching (via deepseek cache_id)
    4. Provides streaming option for real-time responses
    5. Adds support for context windows and conversation history
    """
    
    BASE_URL = "https://api.deepseek.com/v1/chat/completions"
    DEFAULT_MODEL = "deepseek-chat"  # Updated model version
    
    def __init__(self, debug_mode=None):
        """
        Initialize the optimized DeepSeek client with API key from settings.
        
        Args:
            debug_mode: Override debug mode (default: read from settings.DEBUG_LLM)
        """
        super().__init__(debug_mode)
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not self.api_key and not self.debug_mode:
            raise ValueError("DEEPSEEK_API_KEY not found in settings.")
            
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Initialize the context cache
        self._init_context_cache()
    
    def _init_context_cache(self):
        """Initialize the context cache directory for storing conversation history."""
        cache_dir = getattr(settings, 'LLM_CACHE_DIR', os.path.join(settings.BASE_DIR, 'llm_cache'))
        self.context_cache_dir = Path(cache_dir) / 'context_cache'
        self.context_cache_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_context_key(self, context_id: str) -> str:
        """Get cache key for a conversation context."""
        return hashlib.md5(context_id.encode('utf-8')).hexdigest()
    
    def save_context(self, context_id: str, messages: List[Dict[str, str]]) -> None:
        """
        Save conversation history to context cache.
        
        Args:
            context_id: Unique identifier for the conversation
            messages: List of message objects with role and content
        """
        key = self._get_context_key(context_id)
        cache_file = self.context_cache_dir / f"{key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(messages, f)
        except Exception as e:
            logger.warning(f"Failed to save conversation context: {str(e)}")
    
    def load_context(self, context_id: str) -> List[Dict[str, str]]:
        """
        Load conversation history from context cache.
        
        Args:
            context_id: Unique identifier for the conversation
            
        Returns:
            List of message objects with role and content
        """
        key = self._get_context_key(context_id)
        cache_file = self.context_cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return []
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load conversation context: {str(e)}")
            return []
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        structured_output: Dict = None,
        use_cache: bool = True,
        stream: bool = False,
        context_id: str = None,
        cache_id: str = None  # DeepSeek server-side cache identifier
    ) -> Dict:
        """
        Send a prompt to DeepSeek and get a response with optimized caching.
        
        Args:
            system_prompt: Instructions for the LLM on how to respond
            user_prompt: The content to respond to
            model: DeepSeek model to use (default is deepseek-chat)
            max_tokens: Maximum response length
            temperature: Randomness parameter (0-1)
            structured_output: JSON schema for structured output (optional)
            use_cache: Whether to use the cache (default True)
            stream: Whether to stream the response (default False)
            context_id: Unique identifier for conversation context (optional)
            cache_id: DeepSeek server-side cache identifier (optional)
            
        Returns:
            Dict containing the response text and metadata
        """
        model = model or self.DEFAULT_MODEL
        
        # Check if we're in debug mode
        if self.debug_mode:
            logger.info("Using debug mode - returning mock response")
            return self._get_mock_response(system_prompt, user_prompt, model, structured_output)
        
        # Check local cache first if enabled
        if use_cache and temperature < 0.2:  # Only cache deterministic responses
            cache_key_parts = [system_prompt, user_prompt, model]
            if context_id:
                cache_key_parts.append(context_id)
            
            cache_key = "|".join(cache_key_parts)
            cached_response = llm_cache.get_advanced(cache_key)
            if cached_response:
                logger.info("Using cached LLM response (local)")
                return cached_response
        
        # Prepare messages
        messages = []
        
        # Add conversation history if context_id is provided
        if context_id:
            messages = self.load_context(context_id)
            if not messages:
                # If no history exists, start with system message
                messages = [{"role": "system", "content": system_prompt}]
            
            # Add the new user message
            messages.append({"role": "user", "content": user_prompt})
        else:
            # Standard message format without context
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        # Add response format for structured output
        if structured_output:
            payload["response_format"] = {"type": "json_object"}
        
        # Add server-side cache ID if provided
        if cache_id:
            payload["cache_id"] = cache_id
        
        # Retry mechanism
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                    stream=stream
                )
                
                response.raise_for_status()
                
                if stream:
                    # Handle streaming response
                    return self._handle_streaming_response(response)
                else:
                    # Handle regular response
                    result = response.json()
                    
                    # Create response dict
                    response_data = {
                        "content": result["choices"][0]["message"]["content"],
                        "model": result.get("model", model),
                        "usage": result.get("usage", {}),
                        "stop_reason": result["choices"][0].get("finish_reason", None),
                        # Store server-side cache ID if returned
                        "cache_id": result.get("cache_id", None)
                    }
                    
                    # Track server-side cache hits for cost analysis
                    if result.get("usage") and (
                        "prompt_cache_hit_tokens" in result["usage"] or 
                        "prompt_cache_miss_tokens" in result["usage"]
                    ):
                        track_deepseek_server_cache(result["usage"])
                    
                    # Update conversation context if needed
                    if context_id:
                        # Add assistant message to context
                        messages.append({
                            "role": "assistant", 
                            "content": response_data["content"]
                        })
                        # Save updated context
                        self.save_context(context_id, messages)
                    
                    # Cache the response if caching is enabled and the temperature is low enough
                    if use_cache and temperature < 0.2:
                        cache_key = "|".join([system_prompt, user_prompt, model])
                        if context_id:
                            cache_key += f"|{context_id}"
                        llm_cache.set_advanced(cache_key, response_data)
                    
                    return response_data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        # This should never be reached due to the raise in the loop
        raise RuntimeError("Failed to get response from DeepSeek API after multiple attempts")
    
    def _handle_streaming_response(self, response):
        """
        Handle streaming response from DeepSeek API.
        
        Args:
            response: Response object from requests with stream=True
            
        Returns:
            Dict with combined stream content and metadata
        """
        combined_content = ""
        usage = {}
        finish_reason = None
        model = None
        cache_id = None
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                # Skip SSE comments and empty lines
                if line.startswith(':') or not line.strip():
                    continue
                
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    
                    # Check for the [DONE] marker
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data)
                        
                        # Extract content from the chunk
                        if 'choices' in chunk and chunk['choices']:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                combined_content += content
                            
                            # Get finish reason if available
                            if 'finish_reason' in chunk['choices'][0] and chunk['choices'][0]['finish_reason']:
                                finish_reason = chunk['choices'][0]['finish_reason']
                        
                        # Get model name if available
                        if 'model' in chunk and not model:
                            model = chunk['model']
                        
                        # Get usage statistics if available
                        if 'usage' in chunk:
                            usage = chunk['usage']
                        
                        # Get cache_id if available
                        if 'cache_id' in chunk and not cache_id:
                            cache_id = chunk['cache_id']
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming response chunk: {data}")
        
        return {
            "content": combined_content,
            "model": model,
            "usage": usage,
            "stop_reason": finish_reason,
            "cache_id": cache_id
        }
    
    def create_embeddings(self, texts: List[str], model: str = "deepseek-embedding") -> List[List[float]]:
        """
        Create embeddings for the given texts using DeepSeek's embedding model.
        Useful for semantic search and similarity matching.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        if self.debug_mode:
            # Return mock embeddings in debug mode
            return [[0.1] * 128 for _ in texts]
        
        url = "https://api.deepseek.com/v1/embeddings"
        
        payload = {
            "model": model,
            "input": texts
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return [item["embedding"] for item in result["data"]]
        except Exception as e:
            logger.error(f"Failed to create embeddings: {str(e)}")
            raise
    
    def clear_context(self, context_id: str) -> None:
        """
        Clear conversation context for the given context ID.
        
        Args:
            context_id: Unique identifier for the conversation context
        """
        key = self._get_context_key(context_id)
        cache_file = self.context_cache_dir / f"{key}.json"
        
        if cache_file.exists():
            try:
                os.remove(cache_file)
                logger.info(f"Cleared conversation context: {context_id}")
            except Exception as e:
                logger.warning(f"Failed to clear conversation context: {str(e)}")

# Create a global instance for use in other modules
optimized_deepseek_client = OptimizedDeepSeekClient() 