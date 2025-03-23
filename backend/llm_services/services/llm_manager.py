"""
LLM service manager.
Provides utilities for managing LLM service clients and optimizing usage.
"""

import logging
import os
import requests
from typing import Dict, Any, List, Optional
from django.conf import settings
from .llm_client import deepseek_client, claude_client, llm_client
from .optimized_deepseek import optimized_deepseek_client
from .cache import llm_cache

# Setup logging
logger = logging.getLogger(__name__)

class LLMManager:
    """
    Manager for LLM services with optimization and usage tracking.
    Provides a unified interface for working with multiple LLM clients
    and managing caching across providers.
    """
    
    def __init__(self):
        """Initialize the LLM manager."""
        self.deepseek_client = deepseek_client
        self.claude_client = claude_client
        self.optimized_deepseek_client = optimized_deepseek_client
        self.unified_client = llm_client
        
        # Check which providers are available
        self.has_deepseek = getattr(settings, 'DEEPSEEK_API_KEY', '') != ''
        self.has_claude = getattr(settings, 'CLAUDE_API_KEY', '') != ''
        
        # Get default provider from settings, defaulting to Claude if available
        self.default_provider = getattr(settings, 'DEFAULT_LLM_PROVIDER', 'claude' if self.has_claude else 'deepseek').lower()
        
        # Use optimized DeepSeek by default if available
        self.use_optimized_deepseek = getattr(settings, 'USE_OPTIMIZED_DEEPSEEK', True)
        
        # Debug mode
        self.debug_mode = getattr(settings, 'DEBUG_LLM', False)
        
        if self.debug_mode:
            logger.info("LLM Manager initialized in DEBUG mode")
        
        # Log available providers
        provider_info = []
        if self.has_deepseek:
            provider_info.append("DeepSeek")
        if self.has_claude:
            provider_info.append("Claude")
        
        logger.info(f"LLM Manager initialized with providers: {', '.join(provider_info) or 'None'}")
        logger.info(f"Default provider: {self.default_provider}")
        logger.info(f"Using optimized DeepSeek: {self.use_optimized_deepseek}")
    
    def check_claude_balance(self):
        """
        Check the Claude API status and remaining balance.
        
        Returns:
            Dict with status information
        """
        if not self.has_claude:
            return {
                "status": "inactive",
                "message": "Claude API key not configured"
            }
        
        try:
            # We don't have a direct way to check Claude balance
            # So we use a minimal API call to check if it's working
            response = self.claude_client.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Hi",
                max_tokens=1,  # Minimal response to save costs
                temperature=0,
                use_cache=True  # Use cache if available
            )
            
            return {
                "status": "active",
                "message": "Claude API is available and responding"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Claude API error: {str(e)}"
            }
    
    def check_deepseek_balance(self):
        """
        Check the DeepSeek API status and remaining balance.
        
        Returns:
            Dict with status information
        """
        if not self.has_deepseek:
            return {
                "status": "inactive",
                "message": "DeepSeek API key not configured"
            }
        
        try:
            # We don't have a direct way to check DeepSeek balance
            # So we use a minimal API call to check if it's working
            if self.use_optimized_deepseek:
                client = self.optimized_deepseek_client
            else:
                client = self.deepseek_client
                
            response = client.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Hi",
                max_tokens=1,  # Minimal response to save costs
                temperature=0,
                use_cache=True  # Use cache if available
            )
            
            return {
                "status": "active",
                "message": "DeepSeek API is available and responding"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"DeepSeek API error: {str(e)}"
            }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status information for all configured providers.
        
        Returns:
            Dict with provider status information
        """
        status = {
            "default_provider": self.default_provider,
            "providers": {}
        }
        
        if self.has_claude:
            status["providers"]["claude"] = self.check_claude_balance()
        
        if self.has_deepseek:
            status["providers"]["deepseek"] = self.check_deepseek_balance()
        
        return status
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        structured_output: Dict = None,
        use_cache: bool = True,
        provider: str = None,
        context_id: str = None,
        stream: bool = False,
        force_cache: bool = False  # Force using cache even for higher temperatures
    ) -> Dict:
        """
        Generate a response using the appropriate LLM client based on settings.
        
        Args:
            system_prompt: Instructions for the LLM on how to respond
            user_prompt: The content to respond to
            model: LLM model to use (provider-specific)
            max_tokens: Maximum response length
            temperature: Randomness parameter (0-1)
            structured_output: JSON schema for structured output (optional)
            use_cache: Whether to use the cache (default True)
            provider: Override the default provider for this request
            context_id: Unique identifier for conversation context (optional)
            stream: Whether to stream the response (default False)
            force_cache: Whether to force cache use regardless of temperature
            
        Returns:
            Dict containing the response text and metadata
        """
        # Determine which provider to use
        provider = provider.lower() if provider else self.default_provider
        
        # Check for specific scenarios where DeepSeek caching would be beneficial
        should_use_deepseek = False
        
        # If user explicitly asked for DeepSeek
        if provider == 'deepseek' and self.has_deepseek:
            should_use_deepseek = True
        
        # If forcing cache and cache is enabled, use DeepSeek for better caching
        elif force_cache and use_cache and self.has_deepseek:
            should_use_deepseek = True
            provider = 'deepseek'
            logger.info("Forcing DeepSeek for better caching")
        
        # For highly deterministic requests (low temperature), prefer DeepSeek for caching benefits
        elif temperature < 0.2 and use_cache and self.has_deepseek and not provider == 'claude':
            should_use_deepseek = True
            provider = 'deepseek'
            logger.info("Using DeepSeek for low temperature request to leverage caching")
        
        # For conversational contexts, DeepSeek's context caching is beneficial
        elif context_id and self.has_deepseek and not provider == 'claude':
            should_use_deepseek = True
            provider = 'deepseek'
            logger.info("Using DeepSeek for conversation context to leverage caching")
        
        # Use the optimized DeepSeek client if selected
        if should_use_deepseek and self.use_optimized_deepseek:
            logger.info("Using optimized DeepSeek client")
            return optimized_deepseek_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                structured_output=structured_output,
                use_cache=use_cache,
                stream=stream,
                context_id=context_id
            )
        
        # Fall back to the unified client for standard behavior 
        # (including provider fallback if needed)
        return self.unified_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            structured_output=structured_output,
            use_cache=use_cache,
            provider=provider
        )
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        return llm_cache.get_cache_stats_by_provider()
    
    def clear_cache(self, max_age_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Clear cache entries.
        
        Args:
            max_age_seconds: If provided, only clear entries older than this
            
        Returns:
            Dict with results of the clear operation
        """
        # Get stats before clearing
        before_stats = self.get_cache_statistics()
        
        # Clear the cache
        cleared_count = llm_cache.clear(max_age_seconds)
        
        # Get stats after clearing
        after_stats = self.get_cache_statistics()
        
        return {
            "cleared_count": cleared_count,
            "before": before_stats,
            "after": after_stats
        }
    
    def clear_conversation_context(self, context_id: str) -> Dict[str, Any]:
        """
        Clear a specific conversation context.
        
        Args:
            context_id: Unique identifier for the conversation
            
        Returns:
            Dict with result of the clear operation
        """
        if self.use_optimized_deepseek:
            optimized_deepseek_client.clear_context(context_id)
            return {"success": True, "message": f"Context {context_id} cleared"}
        else:
            return {
                "success": False, 
                "message": "Optimized DeepSeek client not enabled, context management unavailable"
            }
    
    def create_embeddings(self, texts: List[str], model: str = "deepseek-embedding") -> List[List[float]]:
        """
        Create embeddings for the given texts.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        if self.use_optimized_deepseek and self.has_deepseek:
            return optimized_deepseek_client.create_embeddings(texts, model)
        else:
            raise NotImplementedError("Embeddings are only available with the optimized DeepSeek client")

# Create a global manager instance
llm_manager = LLMManager() 