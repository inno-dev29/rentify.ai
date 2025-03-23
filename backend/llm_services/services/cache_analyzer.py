"""
Cache analysis utility for measuring LLM cost savings.
Helps track and visualize the cost benefits of the disk caching system.
"""

import os
import json
import time
import datetime
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any
from pathlib import Path
from django.conf import settings

from .cache import llm_cache
from .llm_manager import llm_manager

# Approximate costs per 1M tokens (update as pricing changes)
COST_PER_MILLION_TOKENS = {
    "deepseek": {
        "input": 0.2,  # $0.20 per 1M input tokens
        "output": 1.0,  # $1.00 per 1M output tokens
        "cache_hit": 0.014  # $0.014 per 1M tokens for cache hits
    },
    "claude": {
        "input": 3.0,  # $3.00 per 1M input tokens
        "output": 15.0,  # $15.00 per 1M output tokens
    }
}

def format_size(size_bytes: int) -> str:
    """Format byte size to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def format_usd(amount: float) -> str:
    """Format amount as USD."""
    return f"${amount:.2f}"

def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    This is a rough approximation (4 chars ≈ 1 token).
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    return len(text) // 4

def analyze_cache_savings() -> Dict[str, Any]:
    """
    Analyze the cache to estimate cost savings.
    
    Returns:
        Dictionary with analysis results
    """
    if not os.path.exists(llm_cache.cache_dir):
        return {
            "cache_hits": 0,
            "estimated_savings": 0.0,
            "provider_savings": {},
            "cached_tokens": {"input": 0, "output": 0},
            "server_cache": {},
            "cache_size": 0,
            "cache_entries": 0
        }
    
    cache_files = list(Path(llm_cache.cache_dir).glob("*.json"))
    
    total_input_tokens = 0
    total_output_tokens = 0
    provider_tokens = {
        "deepseek": {"input": 0, "output": 0},
        "claude": {"input": 0, "output": 0},
        "unknown": {"input": 0, "output": 0}
    }
    
    total_hits = 0
    provider_hits = {
        "deepseek": 0,
        "claude": 0,
        "unknown": 0
    }
    
    # Load the cache metadata if it exists
    metadata_file = Path(llm_cache.cache_dir) / "cache_metadata.json"
    metadata = {}
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {}
    
    for file_path in cache_files:
        if file_path.name == "cache_metadata.json":
            continue
            
        try:
            with open(file_path, 'r') as f:
                cache_data = json.load(f)
                
                # Get provider from model name
                model = cache_data.get("model", "").lower()
                if "deepseek" in model:
                    provider = "deepseek"
                elif "claude" in model:
                    provider = "claude"
                else:
                    provider = "unknown"
                
                # Get token usage
                usage = cache_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                
                # If token counts not available, estimate them
                if input_tokens == 0 and "system_prompt" in cache_data and "user_prompt" in cache_data:
                    combined_input = cache_data.get("system_prompt", "") + cache_data.get("user_prompt", "")
                    input_tokens = estimate_tokens(combined_input)
                
                if output_tokens == 0 and "content" in cache_data:
                    output_tokens = estimate_tokens(cache_data.get("content", ""))
                
                # Get hit count from metadata or default to 1
                cache_key = file_path.stem
                hit_count = metadata.get("hit_counts", {}).get(cache_key, 1)
                
                # Update totals
                total_input_tokens += input_tokens * (hit_count - 1)  # Subtract first call which isn't saved
                total_output_tokens += output_tokens * (hit_count - 1)
                
                provider_tokens[provider]["input"] += input_tokens * (hit_count - 1)
                provider_tokens[provider]["output"] += output_tokens * (hit_count - 1)
                
                total_hits += hit_count - 1
                provider_hits[provider] += hit_count - 1
                
        except Exception as e:
            # Skip corrupted cache files
            continue
    
    # Calculate cost savings
    savings = 0.0
    provider_savings = {}
    
    for provider, tokens in provider_tokens.items():
        if provider == "unknown":
            continue
            
        input_cost = tokens["input"] * COST_PER_MILLION_TOKENS[provider]["input"] / 1_000_000
        output_cost = tokens["output"] * COST_PER_MILLION_TOKENS[provider]["output"] / 1_000_000
        
        provider_savings[provider] = input_cost + output_cost
        savings += input_cost + output_cost
    
    # before return, add server cache statistics if available
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            # Add server cache stats if available
            if "server_cache_stats" in metadata:
                server_stats = metadata["server_cache_stats"]
                savings += server_stats.get("estimated_savings", 0.0)
                
                # Add to provider stats
                if "deepseek" in provider_savings:
                    provider_savings["deepseek"] += server_stats.get("estimated_savings", 0.0)
                else:
                    provider_savings["deepseek"] = server_stats.get("estimated_savings", 0.0)
        except:
            pass
    
    # Get total cache size
    cache_size = sum(os.path.getsize(f) for f in cache_files if f.name != "cache_metadata.json")
    
    return {
        "cache_hits": total_hits,
        "estimated_savings": savings,
        "provider_savings": provider_savings,
        "cached_tokens": {
            "input": total_input_tokens,
            "output": total_output_tokens
        },
        "server_cache": metadata.get("server_cache_stats", {}) if "metadata" in locals() else {},
        "cache_size": cache_size,
        "cache_entries": len(cache_files)
    }

def update_hit_count(cache_key: str):
    """
    Update the hit count for a cache entry.
    
    Args:
        cache_key: The cache key that was hit
    """
    metadata_file = Path(llm_cache.cache_dir) / "cache_metadata.json"
    metadata = {}
    
    # Load existing metadata if available
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {}
    
    # Initialize hit_counts if not present
    if "hit_counts" not in metadata:
        metadata["hit_counts"] = {}
    
    # Update hit count
    if cache_key in metadata["hit_counts"]:
        metadata["hit_counts"][cache_key] += 1
    else:
        metadata["hit_counts"][cache_key] = 1
    
    # Save updated metadata
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
    except Exception as e:
        from logging import getLogger
        logger = getLogger(__name__)
        logger.warning(f"Failed to update cache hit counts: {str(e)}")

def register_cache_hit(system_prompt: str, user_prompt: str, model: str):
    """
    Register a cache hit for tracking statistics.
    
    Args:
        system_prompt: System instructions
        user_prompt: User query
        model: LLM model name
    """
    cache_key = llm_cache.get_cache_key(system_prompt, user_prompt, model)
    update_hit_count(cache_key)

def print_savings_report():
    """
    Print a report of estimated cost savings from the cache.
    """
    analysis = analyze_cache_savings()
    
    print("\n====== LLM CACHE SAVINGS REPORT ======\n")
    print(f"Total cache entries: {analysis['cache_entries']}")
    print(f"Total cache size: {format_size(analysis['cache_size'])}")
    print(f"Cache hits: {analysis['cache_hits']}")
    
    print("\nEstimated token savings:")
    print(f"  Input tokens: {analysis['cached_tokens']['input']:,}")
    print(f"  Output tokens: {analysis['cached_tokens']['output']:,}")
    
    print("\nEstimated cost savings:")
    print(f"  Total: {format_usd(analysis['estimated_savings'])}")
    
    for provider, amount in analysis['provider_savings'].items():
        if amount > 0:
            print(f"  {provider.capitalize()}: {format_usd(amount)}")
    
    print("\n======================================\n")

def generate_savings_chart(output_file: str = None):
    """
    Generate a chart showing the cost savings over time.
    
    Args:
        output_file: Path to save the chart (default: cache_savings.png in cache dir)
    """
    if not output_file:
        output_file = os.path.join(llm_cache.cache_dir, "cache_savings.png")
    
    # Collect data for the chart
    metadata_file = Path(llm_cache.cache_dir) / "cache_metadata.json"
    if not metadata_file.exists():
        print("No cache metadata available for charting")
        return
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except:
        print("Error reading cache metadata")
        return
    
    if "daily_stats" not in metadata:
        print("No daily statistics available for charting")
        return
    
    daily_stats = metadata["daily_stats"]
    
    # Prepare data for plotting
    dates = []
    daily_savings = []
    cumulative_savings = []
    running_total = 0
    
    for date_str, stats in sorted(daily_stats.items()):
        dates.append(date_str)
        daily_amount = stats.get("savings", 0)
        daily_savings.append(daily_amount)
        running_total += daily_amount
        cumulative_savings.append(running_total)
    
    # Create the chart
    plt.figure(figsize=(12, 6))
    
    # Bar chart for daily savings
    plt.bar(dates, daily_savings, alpha=0.6, label="Daily Savings")
    
    # Line chart for cumulative savings
    plt.plot(dates, cumulative_savings, color='red', marker='o', label="Cumulative Savings")
    
    # Add labels and title
    plt.xlabel("Date")
    plt.ylabel("Cost Savings (USD)")
    plt.title("LLM Cache Cost Savings Over Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add annotations
    plt.annotate(f"Total: ${running_total:.2f}", 
                xy=(dates[-1], cumulative_savings[-1]),
                xytext=(10, 10),
                textcoords="offset points",
                arrowprops=dict(arrowstyle="->"))
    
    plt.tight_layout()
    
    # Save the chart
    plt.savefig(output_file)
    print(f"Savings chart saved to {output_file}")

def update_daily_statistics():
    """
    Update the daily statistics in the cache metadata.
    Call this once per day (e.g., from a cron job).
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Get current analysis
    analysis = analyze_cache_savings()
    
    # Load existing metadata
    metadata_file = Path(llm_cache.cache_dir) / "cache_metadata.json"
    metadata = {}
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {}
    
    # Initialize daily_stats if not present
    if "daily_stats" not in metadata:
        metadata["daily_stats"] = {}
    
    # Initialize previous day's cumulative savings
    prev_total = 0
    for date_str, stats in metadata["daily_stats"].items():
        if date_str < today:
            prev_total += stats.get("savings", 0)
    
    # Calculate today's incremental savings
    todays_savings = analysis["estimated_savings"] - prev_total
    if todays_savings < 0:
        todays_savings = 0  # Prevent negative values
    
    # Update today's stats
    metadata["daily_stats"][today] = {
        "cache_hits": analysis["cache_hits"],
        "input_tokens": analysis["cached_tokens"]["input"],
        "output_tokens": analysis["cached_tokens"]["output"],
        "savings": todays_savings
    }
    
    # Save updated metadata
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
    except Exception as e:
        from logging import getLogger
        logger = getLogger(__name__)
        logger.warning(f"Failed to update daily cache statistics: {str(e)}")

# Patch the cache.get method to track hits
original_get = llm_cache.get

def patched_get(self, system_prompt: str, user_prompt: str, model: str):
    """Patched version of get that tracks cache hits."""
    result = original_get(self, system_prompt, user_prompt, model)
    if result:
        register_cache_hit(system_prompt, user_prompt, model)
    return result

# Apply the patch
llm_cache.get = patched_get.__get__(llm_cache, type(llm_cache))

def track_deepseek_server_cache(usage_data: Dict[str, Any]) -> None:
    """
    Track DeepSeek server-side cache hits.
    
    Args:
        usage_data: Usage data from the DeepSeek API response
    """
    if not usage_data:
        return
        
    # Check for DeepSeek cache hit/miss tokens
    cache_hit_tokens = usage_data.get("prompt_cache_hit_tokens", 0)
    cache_miss_tokens = usage_data.get("prompt_cache_miss_tokens", 0)
    
    if cache_hit_tokens == 0 and cache_miss_tokens == 0:
        return  # No cache-related data in this response
    
    # Calculate savings from cache hits
    regular_cost = cache_hit_tokens * COST_PER_MILLION_TOKENS["deepseek"]["input"] / 1_000_000
    cache_cost = cache_hit_tokens * COST_PER_MILLION_TOKENS["deepseek"]["cache_hit"] / 1_000_000
    savings = regular_cost - cache_cost
    
    # Load existing server cache statistics
    metadata_file = Path(llm_cache.cache_dir) / "cache_metadata.json"
    metadata = {}
    
    # Load existing metadata if available
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {}
    
    # Initialize server cache stats if not present
    if "server_cache_stats" not in metadata:
        metadata["server_cache_stats"] = {
            "total_hit_tokens": 0,
            "total_miss_tokens": 0,
            "estimated_savings": 0.0,
            "total_requests": 0
        }
    
    # Update server cache statistics
    stats = metadata["server_cache_stats"]
    stats["total_hit_tokens"] += cache_hit_tokens
    stats["total_miss_tokens"] += cache_miss_tokens
    stats["estimated_savings"] += savings
    stats["total_requests"] += 1
    
    # Save updated metadata
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
    except Exception as e:
        from logging import getLogger
        logger = getLogger(__name__)
        logger.warning(f"Failed to update server cache statistics: {str(e)}") 