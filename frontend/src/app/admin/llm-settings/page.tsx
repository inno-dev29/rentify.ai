'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { llmService } from '@/app/api/services/llmService';

export default function LLMSettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [providerInfo, setProviderInfo] = useState<any>(null);

  useEffect(() => {
    fetchProviderInfo();
  }, []);

  const fetchProviderInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const info = await llmService.getProviderInfo();
      setProviderInfo(info);
    } catch (err) {
      console.error('Error fetching provider info:', err);
      setError('Failed to load LLM provider information');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto my-8 px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">LLM Provider Settings</h1>
          <button
            onClick={() => router.push('/admin')}
            className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white"
          >
            Back to Admin
          </button>
        </div>
        <div className="animate-pulse p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto my-8 px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">LLM Provider Settings</h1>
          <button
            onClick={() => router.push('/admin')}
            className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white"
          >
            Back to Admin
          </button>
        </div>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p>{error}</p>
          <button 
            onClick={fetchProviderInfo}
            className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto my-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">LLM Provider Settings</h1>
        <button
          onClick={() => router.push('/admin')}
          className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white"
        >
          Back to Admin
        </button>
      </div>
      
      <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Provider Configuration</h2>
        
        {providerInfo && (
          <div className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">Default Provider</h3>
              <p className="bg-gray-100 dark:bg-gray-700 p-3 rounded">
                {providerInfo.default_provider || 'None configured'}
              </p>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Available Providers</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {providerInfo.providers && Object.entries(providerInfo.providers).map(([name, info]: [string, any]) => (
                  <div key={name} className="border dark:border-gray-700 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium capitalize">{name}</span>
                      <span className={`px-2 py-1 text-xs rounded ${info.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {info.available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <p>Model: {info.model || 'Not specified'}</p>
                      <p>API Key: {info.api_key ? '••••••••' : 'Not configured'}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Cache Settings</h3>
              <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded">
                <p>Cache Enabled: {providerInfo.cache_enabled ? 'Yes' : 'No'}</p>
                <p>Cache TTL: {providerInfo.cache_ttl || 'Default'}</p>
                <p>Cache Directory: {providerInfo.cache_directory || 'Default'}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 