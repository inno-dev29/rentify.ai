#!/usr/bin/env python3
"""
LLM Cache Management Script for rentify.ai.

This script provides commands for managing the LLM response cache
and conversation contexts used by DeepSeek and Claude.

Usage:
  python manage_llm_cache.py stats                    # Show cache statistics
  python manage_llm_cache.py clear                    # Clear all cache entries
  python manage_llm_cache.py clear --days 7           # Clear entries older than 7 days
  python manage_llm_cache.py clear --hours 12         # Clear entries older than 12 hours
  python manage_llm_cache.py list                     # List all cache entries
  python manage_llm_cache.py contexts list            # List all conversation contexts
  python manage_llm_cache.py contexts clear <id>      # Clear a specific context
  python manage_llm_cache.py contexts clear --all     # Clear all conversation contexts
  python manage_llm_cache.py optimize                 # Run cache optimization
"""

import os
import sys
import json
import time
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Add Django path and setup
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from django.conf import settings
from llm_services.services.cache import llm_cache
from llm_services.services.llm_manager import llm_manager
from llm_services.services.optimized_deepseek import optimized_deepseek_client

def format_size(size_bytes: int) -> str:
    """
    Format byte size to a human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def parse_timestamp(timestamp: float) -> str:
    """
    Convert a Unix timestamp to a formatted date string.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted date string
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the cache.
    
    Returns:
        Dictionary with cache statistics
    """
    return llm_manager.get_cache_statistics()

def print_cache_stats() -> None:
    """
    Print cache statistics to the console.
    """
    stats = get_cache_stats()
    
    print("\nLLM CACHE STATISTICS")
    print("====================")
    
    # Print total stats
    print(f"\nTotal entries: {stats['total']['entry_count']}")
    print(f"Total size: {format_size(stats['total']['total_size'])}")
    
    if stats['total']['oldest_entry']:
        print(f"Oldest entry: {parse_timestamp(stats['total']['oldest_entry'])}")
        print(f"Newest entry: {parse_timestamp(stats['total']['newest_entry'])}")
    
    # Print provider-specific stats
    for provider, data in stats['providers'].items():
        if data['count'] > 0:
            print(f"\n{provider.capitalize()} cache:")
            print(f"  Entries: {data['count']} ({data['count']/stats['total']['entry_count']*100:.1f}% of total)")
            print(f"  Size: {format_size(data['size'])} ({data['size']/stats['total']['total_size']*100:.1f}% of total)")

def clear_cache(max_age=None) -> Tuple[int, int]:
    """
    Clear cache entries.
    
    Args:
        max_age: Maximum age in seconds for entries to keep (None means clear all)
        
    Returns:
        Tuple of (entries_removed, bytes_freed)
    """
    # Get stats before clearing
    before_stats = get_cache_stats()
    total_entries = before_stats['total']['entry_count']
    total_size = before_stats['total']['total_size']
    
    # Clear the cache
    result = llm_manager.clear_cache(max_age)
    cleared_count = result.get('cleared_count', 0)
    
    # Get stats after clearing
    after_stats = get_cache_stats()
    bytes_freed = total_size - after_stats['total']['total_size']
    
    return cleared_count, bytes_freed

def list_cache_entries() -> None:
    """
    List all cache entries with details.
    """
    if not os.path.exists(llm_cache.cache_dir):
        print("Cache directory does not exist.")
        return
    
    cache_files = list(Path(llm_cache.cache_dir).glob("*.json"))
    
    if not cache_files:
        print("No cache entries found.")
        return
    
    print(f"\n{'=' * 30} LLM CACHE ENTRIES {'=' * 31}")
    print(f"{'KEY':<45} {'PROVIDER':<10} {'SIZE':<8} {'DATE':<20} {'CONTENT PREVIEW'}")
    print(f"{'-' * 45} {'-' * 10} {'-' * 8} {'-' * 20} {'-' * 30}")
    
    for file_path in sorted(cache_files, key=os.path.getmtime, reverse=True):
        file_name = os.path.basename(file_path)
        key = os.path.splitext(file_name)[0]
        size = format_size(os.path.getsize(file_path))
        mod_time = parse_timestamp(os.path.getmtime(file_path))
        
        try:
            with open(file_path, 'r') as f:
                cache_data = json.load(f)
                model = cache_data.get("model", "unknown")
                content = cache_data.get("content", "")
                
                # Determine provider
                if "deepseek" in model.lower():
                    provider = "DeepSeek"
                elif "claude" in model.lower():
                    provider = "Claude"
                else:
                    provider = "Unknown"
                
                # Truncate content for display
                if len(content) > 50:
                    content_preview = content[:47] + "..."
                else:
                    content_preview = content
                
                print(f"{key[:45]:<45} {provider:<10} {size:<8} {mod_time:<20} {content_preview}")
        except Exception as e:
            print(f"{key[:45]:<45} {'ERROR':<10} {size:<8} {mod_time:<20} {str(e)}")
    
    print(f"{'=' * 80}")

def list_contexts() -> None:
    """
    List all conversation contexts.
    """
    # Check if optimized client is enabled
    if not getattr(settings, 'USE_OPTIMIZED_DEEPSEEK', True):
        print("Context management is only available with the optimized DeepSeek client.")
        return
    
    context_dir = optimized_deepseek_client.context_cache_dir
    if not os.path.exists(context_dir):
        print("Context directory does not exist.")
        return
    
    context_files = list(Path(context_dir).glob("*.json"))
    
    if not context_files:
        print("No conversation contexts found.")
        return
    
    print(f"\n{'=' * 30} CONVERSATION CONTEXTS {'=' * 30}")
    print(f"{'KEY':<45} {'MESSAGES':<10} {'SIZE':<8} {'LAST MODIFIED':<20}")
    print(f"{'-' * 45} {'-' * 10} {'-' * 8} {'-' * 20}")
    
    for file_path in sorted(context_files, key=os.path.getmtime, reverse=True):
        file_name = os.path.basename(file_path)
        key = os.path.splitext(file_name)[0]
        size = format_size(os.path.getsize(file_path))
        mod_time = parse_timestamp(os.path.getmtime(file_path))
        
        try:
            with open(file_path, 'r') as f:
                context_data = json.load(f)
                message_count = len(context_data)
                
                print(f"{key[:45]:<45} {message_count:<10} {size:<8} {mod_time:<20}")
        except Exception as e:
            print(f"{key[:45]:<45} {'ERROR':<10} {size:<8} {mod_time:<20} {str(e)}")
    
    print(f"{'=' * 80}")

def clear_context(context_id=None, clear_all=False) -> int:
    """
    Clear one or all conversation contexts.
    
    Args:
        context_id: ID of the context to clear (None if clear_all is True)
        clear_all: Whether to clear all contexts
        
    Returns:
        Number of contexts cleared
    """
    # Check if optimized client is enabled
    if not getattr(settings, 'USE_OPTIMIZED_DEEPSEEK', True):
        print("Context management is only available with the optimized DeepSeek client.")
        return 0
    
    context_dir = optimized_deepseek_client.context_cache_dir
    if not os.path.exists(context_dir):
        print("Context directory does not exist.")
        return 0
    
    cleared_count = 0
    
    if clear_all:
        # Clear all contexts
        context_files = list(Path(context_dir).glob("*.json"))
        for file_path in context_files:
            try:
                os.remove(file_path)
                cleared_count += 1
            except Exception as e:
                print(f"Error clearing context {file_path}: {str(e)}")
    elif context_id:
        # Clear specific context
        result = llm_manager.clear_conversation_context(context_id)
        if result.get("success", False):
            cleared_count = 1
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    return cleared_count

def optimize_cache() -> None:
    """
    Perform cache optimization tasks.
    """
    print("\nOptimizing LLM cache...")
    
    # Get initial stats
    before_stats = get_cache_stats()
    
    # 1. Remove any 0-byte or corrupted files
    cache_dir = llm_cache.cache_dir
    if os.path.exists(cache_dir):
        removed = 0
        for file_path in Path(cache_dir).glob("*.json"):
            try:
                # Check if file is empty or corrupted
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    removed += 1
                    continue
                
                # Try to load the JSON to check if it's valid
                with open(file_path, 'r') as f:
                    json.load(f)
            except (json.JSONDecodeError, Exception):
                try:
                    os.remove(file_path)
                    removed += 1
                except:
                    pass
        
        print(f"Removed {removed} corrupted cache files")
    
    # 2. Clear very old entries (older than 30 days)
    old_entries, old_size = clear_cache(max_age=30*24*60*60)  # 30 days
    if old_entries > 0:
        print(f"Cleared {old_entries} entries older than 30 days ({format_size(old_size)})")
    
    # 3. Get final stats
    after_stats = get_cache_stats()
    
    print(f"\nCache optimization complete!")
    print(f"Before: {before_stats['total']['entry_count']} entries, {format_size(before_stats['total']['total_size'])}")
    print(f"After: {after_stats['total']['entry_count']} entries, {format_size(after_stats['total']['total_size'])}")

def provider_status() -> None:
    """
    Display status information for LLM providers.
    Shows active providers and current selection strategy.
    """
    from llm_services.services.llm_manager import llm_manager
    
    print("\n=== LLM Provider Status ===\n")
    
    # Get status from manager
    status = llm_manager.get_provider_status()
    
    print(f"Default provider: {status['default_provider'].upper()}")
    print()
    
    # Display providers
    for provider, info in status['providers'].items():
        print(f"{provider.upper()} provider:")
        if 'error' in info:
            print(f"  Status: Not configured ({info['error']})")
        else:
            print(f"  Status: {info['status']}")
            print(f"  Info: {info['message']}")
        print()
    
    print("\n=== Provider Selection Strategy ===\n")
    print("Current strategy:")
    
    # Explain the current selection strategy
    print("1. Use Claude as the default provider for most requests.")
    print("2. Use optimized DeepSeek with disk caching for:")
    print("   - Requests with low temperature (< 0.2)")
    print("   - Requests with conversation contexts")
    print("   - Requests that explicitly force caching")
    print("3. Fall back to alternative providers if primary fails")
    
    print("\nThis strategy optimizes cost while leveraging DeepSeek's caching capabilities.\n")

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Manage LLM response cache and conversation contexts.')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear cache entries')
    group = clear_parser.add_mutually_exclusive_group()
    group.add_argument('--days', type=int, help='Clear entries older than this many days')
    group.add_argument('--hours', type=int, help='Clear entries older than this many hours')
    
    # List command
    subparsers.add_parser('list', help='List all cache entries')
    
    # Contexts command
    contexts_parser = subparsers.add_parser('contexts', help='Manage conversation contexts')
    contexts_subparsers = contexts_parser.add_subparsers(dest='contexts_command', help='Contexts command to run')
    
    # Contexts list command
    contexts_subparsers.add_parser('list', help='List all conversation contexts')
    
    # Contexts clear command
    contexts_clear_parser = contexts_subparsers.add_parser('clear', help='Clear conversation contexts')
    contexts_clear_parser.add_argument('context_id', nargs='?', help='ID of the context to clear')
    contexts_clear_parser.add_argument('--all', action='store_true', help='Clear all contexts')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Run cache optimization')
    
    # Provider status command
    subparsers.add_parser('providers', help='Display LLM provider status')
    
    # Savings command
    savings_parser = subparsers.add_parser('savings', help='Show LLM cost savings')
    savings_parser.add_argument('--chart', action='store_true', help='Generate a savings chart')
    
    return parser.parse_args()

def main():
    """
    Main entry point for the script.
    """
    args = parse_args()
    
    if args.command == 'stats':
        # Show cache statistics
        print_cache_stats()
    
    elif args.command == 'clear':
        # Clear cache
        if args.days:
            max_age = args.days * 24 * 60 * 60  # Convert days to seconds
            print(f"Clearing cache entries older than {args.days} days...")
        elif args.hours:
            max_age = args.hours * 60 * 60  # Convert hours to seconds
            print(f"Clearing cache entries older than {args.hours} hours...")
        else:
            max_age = None
            print("Clearing all cache entries...")
        
        cleared_count, bytes_freed = clear_cache(max_age)
        
        print(f"Cleared {cleared_count} cache entries ({format_size(bytes_freed)})")
    
    elif args.command == 'list':
        # List cache entries
        list_cache_entries()
    
    elif args.command == 'contexts':
        if args.contexts_command == 'list':
            # List contexts
            list_contexts()
        
        elif args.contexts_command == 'clear':
            # Clear contexts
            if args.all:
                print("Clearing all conversation contexts...")
                cleared_count = clear_context(clear_all=True)
                print(f"Cleared {cleared_count} conversation contexts")
            elif args.context_id:
                print(f"Clearing conversation context: {args.context_id}")
                cleared_count = clear_context(context_id=args.context_id)
                if cleared_count > 0:
                    print(f"Successfully cleared context {args.context_id}")
                else:
                    print(f"Failed to clear context {args.context_id}")
            else:
                print("Error: Must specify a context ID or --all")
                return 1
    
    elif args.command == 'optimize':
        # Optimize cache
        optimize_cache()
    
    elif args.command == 'providers':
        # Display provider status
        provider_status()
    
    elif args.command == 'savings':
        from llm_services.services.cache_analyzer import print_savings_report, generate_savings_chart, update_daily_statistics
        
        # Update daily statistics
        update_daily_statistics()
        
        # Show savings report
        print_savings_report()
        
        # Generate chart if requested
        if args.chart:
            generate_savings_chart()
    
    else:
        # No command specified
        print(__doc__)
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 