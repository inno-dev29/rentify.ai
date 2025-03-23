'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/app/context/AuthContext';
import { ReactNode, useEffect } from 'react';

export default function AdminLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    // Redirect if not admin
    if (!isLoading && (!isAuthenticated || !user?.is_staff)) {
      router.push(isAuthenticated ? '/' : '/login?redirect=/admin');
    }
  }, [isAuthenticated, isLoading, router, user]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Don't render anything until we're sure the user is authenticated and an admin
  if (!isAuthenticated || !user?.is_staff) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/admin" className="text-xl font-bold text-gray-800 dark:text-white">
                Admin Dashboard
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                Back to Site
              </Link>
              <span className="text-gray-600 dark:text-gray-300">
                {user?.username || 'Admin'}
              </span>
            </div>
          </div>
        </div>
      </nav>
      
      <main>
        {children}
      </main>
    </div>
  );
} 