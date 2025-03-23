'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import apiClient from '@/app/api/apiClient';
import { llmService } from '@/app/api/services/llmService';

interface UserTravelPreferencesProps {
  className?: string;
}

export default function UserTravelPreferences({ className = '' }: UserTravelPreferencesProps) {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState<string>('');
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [savedSuccessfully, setSavedSuccessfully] = useState<boolean>(false);
  const [refreshSuccessfully, setRefreshSuccessfully] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const MAX_CHARACTERS = 300;

  useEffect(() => {
    async function fetchPreferences() {
      try {
        if (!user?.id) return;

        const response = await apiClient.get('/users/me/');
        if (response.profile?.travel_preferences) {
          setPreferences(response.profile.travel_preferences);
        }
      } catch (err) {
        console.error('Error fetching travel preferences:', err);
        setError('Unable to load your travel preferences.');
      }
    }

    fetchPreferences();
  }, [user]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= MAX_CHARACTERS) {
      setPreferences(value);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      
      console.log('Saving travel preferences:', preferences);
      
      const response = await apiClient.put('/users/me/', {
        profile: {
          travel_preferences: preferences
        }
      });
      
      console.log('Save response:', response);
      
      setSavedSuccessfully(true);
      setIsEditing(false);
      
      // Reset success message after 3 seconds
      setTimeout(() => {
        setSavedSuccessfully(false);
      }, 3000);
    } catch (err: any) {
      console.error('Error saving travel preferences:', err);
      
      // Provide more specific error message based on the error structure
      let errorMessage = 'Failed to save your travel preferences. Please try again.';
      
      if (err.status === 400) {
        errorMessage = 'Invalid data format. Please check your input and try again.';
        if (err.errors?.profile?.travel_preferences) {
          errorMessage = `Error: ${err.errors.profile.travel_preferences}`;
        }
      } else if (err.status === 401) {
        errorMessage = 'You need to be logged in to save your preferences.';
      } else if (err.status === 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (err.message) {
        errorMessage = `Error: ${err.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefreshPersona = async () => {
    try {
      if (!user?.id) {
        setError('User ID not found. Please log in again.');
        return;
      }
      
      setIsRefreshing(true);
      setError(null);
      
      console.log('Refreshing persona for user:', user.id);
      
      // Delete the existing persona to trigger regeneration
      const response = await llmService.refreshUserPersona(user.id);
      
      console.log('Refresh persona response:', response);
      
      setRefreshSuccessfully(true);
      
      // Reset success message after 3 seconds
      setTimeout(() => {
        setRefreshSuccessfully(false);
      }, 3000);
    } catch (err: any) {
      console.error('Error refreshing persona:', err);
      
      // Provide more specific error message based on the error structure
      let errorMessage = 'Failed to refresh your travel persona. Please try again.';
      
      if (err.status === 401) {
        errorMessage = 'You need to be logged in to refresh your persona.';
      } else if (err.status === 403) {
        errorMessage = 'You do not have permission to refresh this persona.';
      } else if (err.status === 500) {
        errorMessage = 'Server error while generating your persona. Please try again later.';
      } else if (err.message) {
        errorMessage = `Error: ${err.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 my-6 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">Your Travel Preferences</h3>
        <div className="flex space-x-3">
          {!isEditing && preferences && (
            <button
              onClick={handleRefreshPersona}
              className="text-primary hover:text-primary-dark text-sm font-medium flex items-center"
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <>
                  <span className="mr-1">Refreshing</span>
                  <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                </>
              ) : (
                'Refresh Persona'
              )}
            </button>
          )}
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="text-primary hover:text-primary-dark text-sm font-medium"
            >
              {preferences ? 'Edit' : 'Add Preferences'}
            </button>
          )}
        </div>
      </div>

      {isEditing ? (
        <div className="space-y-4">
          <div className="relative">
            <textarea
              value={preferences}
              onChange={handleInputChange}
              placeholder="Tell us about your travel preferences: What type of places do you like to stay? Any favorite destinations or amenities? Are you a solo traveler or do you travel with family? Do you prefer urban or natural settings?"
              className="w-full p-3 border rounded-md h-32 text-secondary dark:text-gray-200 dark:bg-gray-700 dark:border-gray-600"
              maxLength={MAX_CHARACTERS}
            />
            <div className="text-xs text-gray-500 mt-1 text-right">
              {preferences.length}/{MAX_CHARACTERS} characters
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-white bg-primary rounded-md hover:bg-primary-dark disabled:opacity-50 flex items-center"
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <span className="mr-2">Saving</span>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                </>
              ) : (
                'Save'
              )}
            </button>
          </div>
        </div>
      ) : (
        <div>
          {preferences ? (
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">{preferences}</p>
          ) : (
            <p className="text-gray-500 italic">
              You haven't set any travel preferences yet. This information helps us recommend properties that match your travel style.
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {savedSuccessfully && (
        <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-md">
          Your travel preferences have been saved successfully!
        </div>
      )}

      {refreshSuccessfully && (
        <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-md">
          Your travel persona has been refreshed successfully!
        </div>
      )}
    </div>
  );
} 