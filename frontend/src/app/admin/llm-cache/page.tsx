'use client';

import { useRouter } from 'next/navigation';
import { CacheManager } from '@/components/LLM';

export default function LLMCacheManagementPage() {
  const router = useRouter();

  return (
    <div className="max-w-6xl mx-auto my-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">LLM Cache Management</h1>
        <button
          onClick={() => router.push('/admin')}
          className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white"
        >
          Back to Admin
        </button>
      </div>
      
      <CacheManager />
    </div>
  );
} 