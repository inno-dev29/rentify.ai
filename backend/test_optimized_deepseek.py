#!/usr/bin/env python3
"""
Test script for the optimized DeepSeek LLM client.
This script demonstrates the advanced features of the optimized client
including context windows, streaming, embeddings, and server-side caching.

Run it with:
    python test_optimized_deepseek.py
    
To run with debug mode:
    DEBUG_LLM=True python test_optimized_deepseek.py
"""

import os
import sys
import json
import time
import uuid
import hashlib
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from django.conf import settings
from llm_services.services.optimized_deepseek import optimized_deepseek_client
from llm_services.services.llm_manager import llm_manager
from llm_services.services.cache import llm_cache

def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")

def format_size(size_bytes):
    """Format size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def print_cache_stats():
    """Print cache statistics."""
    stats = llm_manager.get_cache_statistics()
    
    print("\nCache Statistics:")
    print(f"Total entries: {stats['total']['entry_count']}")
    print(f"Total size: {format_size(stats['total']['total_size'])}")
    
    for provider, data in stats['providers'].items():
        if data['count'] > 0:
            print(f"\n{provider.capitalize()} cache:")
            print(f"  Entries: {data['count']}")
            print(f"  Size: {format_size(data['size'])}")

def test_basic_response():
    """Test basic response generation with the optimized client."""
    print_section("Testing Basic Response")
    
    system_prompt = "You are a helpful assistant that provides concise responses."
    user_prompt = "What makes DeepSeek LLM unique? Answer in three brief points."
    
    start_time = time.time()
    response = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7
    )
    elapsed = time.time() - start_time
    
    print(f"Response received in {elapsed:.2f} seconds")
    print(f"Model: {response.get('model', 'unknown')}")
    print(f"Content: {response['content'][:300]}...")
    if response.get('cache_id'):
        print(f"Server cache ID: {response['cache_id']}")
    
    return response

def test_streaming_response():
    """Test streaming response generation."""
    print_section("Testing Streaming Response")
    
    system_prompt = "You are a helpful assistant that provides responses one word at a time."
    user_prompt = "Count from 1 to 10, with each number on a new line."
    
    try:
        response = optimized_deepseek_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            stream=True
        )
        
        print(f"Streaming response completed")
        print(f"Content: {response['content']}")
        return True
    except Exception as e:
        print(f"Error testing streaming: {str(e)}")
        return False

def test_context_window():
    """Test conversation context window."""
    print_section("Testing Conversation Context")
    
    # Generate a unique context ID for this conversation
    context_id = f"test_conversation_{uuid.uuid4().hex[:8]}"
    print(f"Context ID: {context_id}")
    
    system_prompt = "You are a helpful assistant. Maintain a count of how many messages have been exchanged in this conversation."
    
    # First message
    print("\nSending first message...")
    response1 = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt="Hello! Can you introduce yourself?",
        temperature=0.7,
        context_id=context_id
    )
    print(f"Response 1: {response1['content'][:200]}...")
    
    # Second message - should reference the conversation history
    print("\nSending second message...")
    response2 = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt="What's the count of messages exchanged so far?",
        temperature=0.7,
        context_id=context_id
    )
    print(f"Response 2: {response2['content'][:200]}...")
    
    # Third message - should continue the conversation
    print("\nSending third message...")
    response3 = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt="Let's continue our conversation. Tell me what the weather is like today.",
        temperature=0.7,
        context_id=context_id
    )
    print(f"Response 3: {response3['content'][:200]}...")
    
    # Clear the context
    print("\nClearing conversation context...")
    llm_manager.clear_conversation_context(context_id)
    
    # Try one more message after clearing - should start fresh
    print("\nSending message after clearing context...")
    response4 = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt="What's the count now?",
        temperature=0.7,
        context_id=context_id
    )
    print(f"Response 4: {response4['content'][:200]}...")
    
    return True

def test_embeddings():
    """Test embedding generation."""
    print_section("Testing Embeddings")
    
    # Skip in debug mode
    if getattr(settings, 'DEBUG_LLM', False):
        print("Skipping embeddings test in debug mode")
        return True
    
    try:
        texts = [
            "Paris is the capital of France",
            "London is the capital of England",
            "Berlin is the capital of Germany"
        ]
        
        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = optimized_deepseek_client.create_embeddings(texts)
        
        print(f"Embeddings generated successfully")
        print(f"Embedding dimensions: {len(embeddings[0])}")
        
        # Calculate similarities between embeddings
        def calculate_similarity(vec1, vec2):
            """Calculate cosine similarity between two vectors."""
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            return dot_product / (magnitude1 * magnitude2)
        
        sim_1_2 = calculate_similarity(embeddings[0], embeddings[1])
        sim_1_3 = calculate_similarity(embeddings[0], embeddings[2])
        sim_2_3 = calculate_similarity(embeddings[1], embeddings[2])
        
        print("\nSimilarities between texts:")
        print(f"Paris-London: {sim_1_2:.4f}")
        print(f"Paris-Berlin: {sim_1_3:.4f}")
        print(f"London-Berlin: {sim_2_3:.4f}")
        
        return True
    except Exception as e:
        print(f"Error testing embeddings: {str(e)}")
        return False

def test_caching():
    """Test response caching with context."""
    print_section("Testing Advanced Caching")
    
    # Setup unique prompts
    system_prompt = "You are an assistant that provides factual information concisely."
    user_prompt = f"What is the capital of France? Answer in one word. {uuid.uuid4().hex[:6]}"
    context_id = f"test_cache_{uuid.uuid4().hex[:8]}"
    
    # First request - should call the API
    print("\nMaking first request (not cached)...")
    start_time = time.time()
    response1 = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,  # Use 0 for deterministic responses
        use_cache=True,
        context_id=context_id
    )
    time1 = time.time() - start_time
    print(f"First request took {time1:.3f} seconds")
    print(f"Response: {response1['content']}")
    
    # Second request - should use cache
    print("\nMaking second request (should use cache)...")
    start_time = time.time()
    response2 = optimized_deepseek_client.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
        use_cache=True,
        context_id=context_id
    )
    time2 = time.time() - start_time
    print(f"Second request took {time2:.3f} seconds")
    print(f"Response: {response2['content']}")
    print(f"Cache speedup: {time1/time2:.1f}x faster")
    
    return True

def main():
    """Run all tests."""
    # Check environment
    print_section("Test Environment")
    print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Debug mode: {getattr(settings, 'DEBUG_LLM', False)}")
    print(f"DeepSeek API configured: {'✅ Yes' if getattr(settings, 'DEEPSEEK_API_KEY', '') else '❌ No'}")
    print(f"Optimized DeepSeek enabled: {'✅ Yes' if getattr(settings, 'USE_OPTIMIZED_DEEPSEEK', True) else '❌ No'}")
    print(f"Cache directory: {getattr(settings, 'LLM_CACHE_DIR', 'not set')}")
    
    # Print initial cache stats
    print_cache_stats()
    
    # Run tests
    print("\nRunning tests...")
    basic_test = test_basic_response()
    stream_test = test_streaming_response()
    context_test = test_context_window()
    embedding_test = test_embeddings()
    cache_test = test_caching()
    
    # Print final cache stats
    print_section("Cache After Tests")
    print_cache_stats()
    
    # Print summary
    print_section("Test Results")
    print(f"Basic Response: {'✅ PASSED' if basic_test else '❌ FAILED'}")
    print(f"Streaming Response: {'✅ PASSED' if stream_test else '❌ FAILED'}")
    print(f"Context Window: {'✅ PASSED' if context_test else '❌ FAILED'}")
    print(f"Embeddings: {'✅ PASSED' if embedding_test else '❌ FAILED'}")
    print(f"Advanced Caching: {'✅ PASSED' if cache_test else '❌ FAILED'}")
    
    tests_passed = sum([
        bool(basic_test), 
        bool(stream_test), 
        bool(context_test), 
        bool(embedding_test), 
        bool(cache_test)
    ])
    tests_total = 5
    
    print(f"\n{tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 