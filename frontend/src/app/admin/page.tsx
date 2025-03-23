'use client';

import Link from 'next/link';

export default function AdminDashboardPage() {
  return (
    <div className="max-w-6xl mx-auto my-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* LLM Management Card */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-4">LLM Management</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Manage LLM cache, view statistics, and regenerate content.
          </p>
          <div className="flex flex-col space-y-2">
            <Link 
              href="/admin/llm-settings" 
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              LLM Provider Settings
            </Link>
            <Link 
              href="/admin/llm-cache" 
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Cache Management
            </Link>
            <Link 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to regenerate all property summaries? This may take a while.')) {
                  // Call the regenerate endpoint
                }
              }}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Regenerate All Summaries
            </Link>
          </div>
        </div>
        
        {/* User Management Card */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-4">User Management</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            View and manage user accounts and permissions.
          </p>
          <div className="flex flex-col space-y-2">
            <Link 
              href="#" 
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              View All Users
            </Link>
          </div>
        </div>
        
        {/* Content Management Card */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-4">Content Management</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Manage properties, reviews, and bookings.
          </p>
          <div className="flex flex-col space-y-2">
            <Link 
              href="#" 
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Manage Properties
            </Link>
            <Link 
              href="#" 
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Manage Bookings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
} 