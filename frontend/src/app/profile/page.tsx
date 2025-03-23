'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';
import { UserTravelPreferences } from '@/components/LLM';

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login?redirect=/profile');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Your Profile</h1>
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="p-6">
          <div className="flex items-center mb-6">
            <div className="h-20 w-20 rounded-full bg-blue-500 flex items-center justify-center text-white text-3xl font-bold">
              {user?.username?.charAt(0).toUpperCase() || '?'}
            </div>
            <div className="ml-6">
              <h2 className="text-2xl font-semibold">{user?.username}</h2>
              <p className="text-gray-600">{user?.email}</p>
            </div>
          </div>
          
          <div className="border-t pt-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">Account Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Username</p>
                <p className="font-medium">{user?.username}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Email</p>
                <p className="font-medium">{user?.email}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Account Type</p>
                <p className="font-medium">
                  {user?.is_staff ? 'Administrator' : 'Regular User'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Joined</p>
                <p className="font-medium">
                  {user?.date_joined 
                    ? new Date(user.date_joined).toLocaleDateString() 
                    : 'Unknown'}
                </p>
              </div>
            </div>
          </div>
          
          {/* Travel Preferences Section */}
          <div className="border-t pt-6 mt-6">
            <UserTravelPreferences />
          </div>
        </div>
        
        <div className="bg-gray-50 px-6 py-4 border-t">
          <div className="flex justify-end">
            <button
              onClick={() => {/* Edit profile functionality would go here */}}
              className="bg-gray-200 text-gray-800 px-4 py-2 rounded-md mr-3 hover:bg-gray-300"
            >
              Edit Profile
            </button>
            <button
              onClick={() => {/* Change password functionality would go here */}}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Change Password
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 