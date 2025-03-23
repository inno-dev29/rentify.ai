'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { llmService } from '@/app/api/services/llmService';
import { PropertyRecommendation } from '@/types/property';
import { AlertCircle } from 'lucide-react';
import { useAuth } from '@/app/context/AuthContext';

interface PropertyRecommendationsProps {
  userId?: number | string;
  limit?: number;
  className?: string;
  showErrorState?: boolean;
}

export default function PropertyRecommendations({ 
  userId, 
  limit = 4, 
  className = '',
  showErrorState = false
}: PropertyRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<PropertyRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 1;
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    async function fetchRecommendations() {
      // Skip API call if user is not authenticated
      if (!isAuthenticated && !userId) {
        setLoading(false);
        setError('Please log in to see personalized recommendations');
        return;
      }

      try {
        setLoading(true);
        // Only pass userId if it's defined, otherwise get current user recommendations
        const data = userId 
          ? await llmService.getUserRecommendations(userId)
          : await llmService.getRecommendations();
          
        // Check if there's an error message in the response
        if (data.error_message) {
          setError(data.error_message);
          setRecommendations([]);
        } else {
          // Extract the recommendations array from the response
          setRecommendations(data.recommendations?.slice(0, limit) || []);
          setError(null);
        }
      } catch (err) {
        console.error('Error fetching property recommendations:', err);
        setError('Unable to load property recommendations');
        
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
    
    fetchRecommendations();
  }, [userId, limit, retryCount, isAuthenticated]);

  // This effect re-triggers the fetch when retry count changes
  useEffect(() => {
    if (retryCount > 0 && retryCount <= MAX_RETRIES) {
      setLoading(true);
    }
  }, [retryCount]);

  // Don't show anything if user isn't authenticated and we don't want to show errors
  if (!isAuthenticated && !userId && !showErrorState) {
    return null;
  }

  if (loading) {
    return (
      <div className={`${className}`}>
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(limit)].map((_, i) => (
            <div key={i} className="animate-pulse border rounded-lg overflow-hidden">
              <div className="h-48 bg-gray-200 dark:bg-gray-700"></div>
              <div className="p-4">
                <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show error state if showErrorState is true and we have an error
  if (error && showErrorState) {
    const isAuthError = error.includes('log in') || error.includes('authenticated') || !isAuthenticated;
    
    return (
      <div className={`my-8 ${className}`}>
        <h2 className="text-2xl font-bold mb-6">Recommended For You</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 my-4 border border-amber-200 dark:border-amber-800">
          <div className="flex items-center text-amber-600 mb-3">
            <AlertCircle className="w-5 h-5 mr-2" />
            <h3 className="text-lg font-medium">
              {isAuthError ? 'Login Required' : 'Recommendations Unavailable'}
            </h3>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {isAuthError 
              ? 'Please log in to see personalized property recommendations.'
              : 'We\'re having trouble loading personalized recommendations. Please check back later.'}
          </p>
          {isAuthError ? (
            <Link href="/login" className="text-primary hover:text-primary-dark text-sm font-medium">
              Go to login
            </Link>
          ) : (
            <button 
              onClick={() => {setRetryCount(0); setLoading(true);}}
              className="text-primary hover:text-primary-dark text-sm font-medium"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    );
  }

  // If error and showErrorState is false, or if recommendations is empty, don't render anything
  if (error || recommendations.length === 0) {
    return null;
  }

  return (
    <div className={`my-8 ${className}`}>
      <h2 className="text-2xl font-bold mb-6">Recommended For You</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {recommendations.map((property, index) => (
          <div key={`property-${property.property_id}-${index}`} className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            <Link href={`/properties/${property.property_id}`}>
              <div className="relative h-48 bg-gray-200 dark:bg-gray-700">
                {property.primary_image_url ? (
                  <Image
                    src={property.primary_image_url}
                    alt={property.title || `Property ${property.property_id}`}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                    className="object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <span className="text-gray-400">No image</span>
                  </div>
                )}
                <div className="absolute top-2 right-2 bg-primary text-white px-2 py-1 rounded-full text-sm">
                  {property.match_score}% Match
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-lg mb-1">{property.title || `Property ${property.property_id}`}</h3>
                {(property.city || property.country) && (
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">
                    {[property.city, property.country].filter(Boolean).join(', ')}
                  </p>
                )}
                {property.base_price !== undefined && (
                  <p className="font-medium mb-3">${property.base_price} / night</p>
                )}
                
                {property.match_reasons && property.match_reasons.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Why you'll like this:</p>
                    <ul className="text-sm text-gray-600 dark:text-gray-400">
                      {property.match_reasons.slice(0, 1).map((reason, idx) => (
                        <li key={`${property.property_id}-reason-${idx}`} className="mb-1 line-clamp-2">• {reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
} 