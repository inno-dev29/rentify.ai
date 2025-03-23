'use client';

import { useState, useEffect } from 'react';
import { llmService } from '@/app/api/services/llmService';

interface CacheStats {
  entry_count: number;
  total_size_bytes: number;
  provider_stats: {
    [provider: string]: {
      entry_count: number;
      size_bytes: number;
    }
  };
  oldest_entry_timestamp: number;
  newest_entry_timestamp: number;
}

export default function CacheManager() {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [clearingCache, setClearingCache] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchCacheStats();
  }, []);

  const fetchCacheStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await llmService.getCacheStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching cache stats:', err);
      setError('Failed to load cache statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async (options?: { days?: number, hours?: number }) => {
    try {
      setClearingCache(true);
      setError(null);
      setSuccess(null);
      const result = await llmService.clearCache(options);
      setSuccess(`Successfully cleared ${result.entries_removed} cache entries`);
      // Refresh stats after clearing
      fetchCacheStats();
    } catch (err) {
      console.error('Error clearing cache:', err);
      setError('Failed to clear cache');
    } finally {
      setClearingCache(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="animate-pulse p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded"></div>
          ))}
        </div>
        <div className="h-10 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">LLM Cache Manager</h2>
        <button 
          onClick={fetchCacheStats}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg"
        >
          Refresh Stats
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg">
          {success}
        </div>
      )}

      {stats && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Cache Statistics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-gray-500 dark:text-gray-400 text-sm">Total Entries</div>
              <div className="text-2xl font-bold">{stats.entry_count}</div>
            </div>
            
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-gray-500 dark:text-gray-400 text-sm">Total Size</div>
              <div className="text-2xl font-bold">{formatBytes(stats.total_size_bytes)}</div>
            </div>
            
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-gray-500 dark:text-gray-400 text-sm">Oldest Entry</div>
              <div className="text-lg font-bold">{formatDate(stats.oldest_entry_timestamp)}</div>
            </div>
            
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-gray-500 dark:text-gray-400 text-sm">Newest Entry</div>
              <div className="text-lg font-bold">{formatDate(stats.newest_entry_timestamp)}</div>
            </div>
          </div>
          
          {/* Provider Statistics */}
          {stats.provider_stats && Object.keys(stats.provider_stats).length > 0 && (
            <div className="mb-6">
              <h4 className="text-md font-semibold mb-3">Provider Statistics</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Provider
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Entries
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Size
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {Object.entries(stats.provider_stats).map(([provider, providerStats]) => (
                      <tr key={provider}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium">{provider}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm">{providerStats.entry_count}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm">{formatBytes(providerStats.size_bytes)}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-4">Cache Management</h3>
        
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => handleClearCache()}
            disabled={clearingCache}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {clearingCache ? 'Clearing...' : 'Clear All Cache'}
          </button>
          
          <button
            onClick={() => handleClearCache({ days: 7 })}
            disabled={clearingCache}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
          >
            {clearingCache ? 'Clearing...' : 'Clear Entries Older Than 7 Days'}
          </button>
          
          <button
            onClick={() => handleClearCache({ hours: 24 })}
            disabled={clearingCache}
            className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50"
          >
            {clearingCache ? 'Clearing...' : 'Clear Entries Older Than 24 Hours'}
          </button>
          
          <button
            onClick={() => llmService.regenerateSummaries()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Regenerate All Property Summaries
          </button>
        </div>
      </div>
    </div>
  );
} 