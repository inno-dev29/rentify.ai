'use client';

import { useState, useEffect } from 'react';
import { llmService } from '@/app/api/services/llmService';
import { UserPersona as UserPersonaType } from '@/types/property';
import { AlertCircle } from 'lucide-react';
import LoadingBar from '@/components/ui/LoadingBar';

interface UserPersonaProps {
  userId?: number | string;
  className?: string;
  showErrorState?: boolean; // Control whether to show error message or hide component on error
}

export default function UserPersona({ 
  userId, 
  className = '', 
  showErrorState = false 
}: UserPersonaProps) {
  const [persona, setPersona] = useState<UserPersonaType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 1;

  useEffect(() => {
    async function fetchPersona() {
      try {
        setLoading(true);
        const data = await llmService.getUserPersona(userId);
        setPersona(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching user persona:', err);
        setError('Unable to load user persona');
        
        // Retry once after a short delay if we haven't reached max retries
        if (retryCount < MAX_RETRIES) {
          const timer = setTimeout(() => {
            setRetryCount(prevCount => prevCount + 1);
          }, 2000);
          return () => clearTimeout(timer);
        }
      } finally {
        setLoading(false);
      }
    }
    
    fetchPersona();
  }, [userId, retryCount]);

  // This effect re-triggers the fetch when retry count changes
  useEffect(() => {
    if (retryCount > 0 && retryCount <= MAX_RETRIES) {
      setLoading(true);
    }
  }, [retryCount]);

  if (loading) {
    return (
      <div className={`${className}`}>
        {/* Add LoadingBar */}
        <LoadingBar isLoading={loading} />
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 my-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3"></div>
                <div className="flex flex-wrap gap-2 mb-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                  ))}
                </div>
              </div>
              <div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
              </div>
            </div>
          </div>
          <div className="mt-6 text-center text-gray-500 dark:text-gray-400">
            <p>Generating travel profile...</p>
            <p className="text-sm mt-1">This may take a few moments</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if showErrorState is true and we have an error
  if (error && showErrorState) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 my-6 ${className}`}>
        <div className="flex items-center text-amber-600 mb-3">
          <AlertCircle className="w-5 h-5 mr-2" />
          <h3 className="text-lg font-medium">Travel Profile Unavailable</h3>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          We're having trouble generating your travel profile at the moment. Please check back later.
        </p>
        <button 
          onClick={() => {setRetryCount(0); setLoading(true);}}
          className="text-primary hover:text-primary-dark text-sm font-medium"
        >
          Try again
        </button>
      </div>
    );
  }

  // If error and showErrorState is false, or if persona is null, don't render anything
  if (error || !persona) {
    return null;
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 my-6 ${className}`}>
      <h3 className="text-xl font-semibold mb-4">Your Travel Profile</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Preferences Section */}
        <div>
          <h4 className="font-medium text-primary mb-2">Your Preferences</h4>
          
          <div className="mb-3">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Property Types</p>
            <div className="flex flex-wrap gap-2">
              {persona.preferences && persona.preferences.property_types && persona.preferences.property_types.length > 0 ? (
                persona.preferences.property_types.map((type, idx) => (
                  <span key={`type-${idx}`} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">
                    {type}
                  </span>
                ))
              ) : (
                <span className="text-gray-400 dark:text-gray-500">No property types specified</span>
              )}
            </div>
          </div>
          
          <div className="mb-3">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Favorite Locations</p>
            <div className="flex flex-wrap gap-2">
              {persona.preferences && persona.preferences.locations && persona.preferences.locations.length > 0 ? (
                persona.preferences.locations.map((location, idx) => (
                  <span key={`loc-${idx}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                    {location}
                  </span>
                ))
              ) : (
                <span className="text-gray-400 dark:text-gray-500">No locations specified</span>
              )}
            </div>
          </div>
          
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Must-Have Amenities</p>
            <div className="flex flex-wrap gap-2">
              {persona.preferences && persona.preferences.amenities && persona.preferences.amenities.length > 0 ? (
                persona.preferences.amenities.map((amenity, idx) => (
                  <span key={`amen-${idx}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                    {amenity}
                  </span>
                ))
              ) : (
                <span className="text-gray-400 dark:text-gray-500">No amenities specified</span>
              )}
            </div>
          </div>
        </div>
        
        {/* Travel Habits Section */}
        <div>
          <h4 className="font-medium text-primary mb-2">Travel Habits</h4>
          
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Typical Group Size</p>
              <p className="text-gray-800 dark:text-gray-200">
                {persona.travel_habits && persona.travel_habits.typical_group_size ? 
                  persona.travel_habits.typical_group_size : 'Not specified'}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Stay Length</p>
              <p className="text-gray-800 dark:text-gray-200">
                {persona.travel_habits && persona.travel_habits.typical_stay_length ? 
                  persona.travel_habits.typical_stay_length : 'Not specified'}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Booking Style</p>
              <p className="text-gray-800 dark:text-gray-200">
                {persona.travel_habits && persona.travel_habits.planning_style ? 
                  persona.travel_habits.planning_style : 'Not specified'}
              </p>
            </div>
          </div>
        </div>
        
        {/* Interests Section */}
        <div>
          <h4 className="font-medium text-primary mb-2">Interests</h4>
          <div className="flex flex-wrap gap-2">
            {persona.interests && persona.interests.length > 0 ? (
              persona.interests.map((interest, idx) => (
                <span key={`int-${idx}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                  {interest}
                </span>
              ))
            ) : (
              <span className="text-gray-400 dark:text-gray-500">No interests specified</span>
            )}
          </div>
        </div>
      </div>
      
      {/* Footer with generation information */}
      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 flex justify-between items-center">
        <div>
          {persona?.model && `Generated by ${persona.model}`} 
          {persona?.generated_at && ` on ${new Date(persona.generated_at).toLocaleDateString()}`}
        </div>
        
        {/* Show creation method if available with color coding */}
        {persona?.created_by && (
          <div className={`text-xs px-2 py-1 rounded ${
            persona.created_by === 'claude' 
              ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
              : persona.created_by === 'claude-fixed' 
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                : persona.created_by === 'regex-extraction'
                  ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
          }`}>
            {persona.created_by}
          </div>
        )}
      </div>
    </div>
  );
} 