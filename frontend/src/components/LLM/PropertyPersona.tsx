'use client';

import { useState, useEffect } from 'react';
import { llmService } from '@/app/api/services/llmService';
import { PropertyPersona as PropertyPersonaType } from '@/types/property';
import LoadingBar from '@/components/ui/LoadingBar';
import { AlertCircle } from 'lucide-react';

interface PropertyPersonaProps {
  propertyId: number | string;
  className?: string;
  showErrorState?: boolean; // Control whether to show error message or hide component on error
}

export default function PropertyPersona({ 
  propertyId, 
  className = '', 
  showErrorState = false 
}: PropertyPersonaProps) {
  const [persona, setPersona] = useState<PropertyPersonaType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 1;

  useEffect(() => {
    async function fetchPersona() {
      try {
        setLoading(true);
        const data = await llmService.getPropertyPersona(propertyId);
        setPersona(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching property persona:', err);
        setError('Unable to load property persona');
        
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
  }, [propertyId, retryCount]);

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
                    <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                  ))}
                </div>
              </div>
              <div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                <div className="flex flex-wrap gap-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 text-center text-gray-500 dark:text-gray-400">
            <p>Generating property persona...</p>
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
          <h3 className="text-lg font-medium">Property Profile Unavailable</h3>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          We're having trouble generating a property profile at the moment. Please check back later.
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
      <h3 className="text-xl font-semibold mb-4">Perfect For</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ideal Guests Section */}
        {persona.ideal_guests && (
          <div>
            <h4 className="font-medium text-primary mb-2">Ideal For</h4>
            {persona.ideal_guests.demographics && (
              <div className="flex flex-wrap gap-2 mb-3">
                {persona.ideal_guests.demographics.map((item, idx) => (
                  <span key={`demo-${idx}`} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">
                    {item}
                  </span>
                ))}
              </div>
            )}
            {persona.ideal_guests.traveler_types && (
              <div className="flex flex-wrap gap-2">
                {persona.ideal_guests.traveler_types.map((item, idx) => (
                  <span key={`traveler-${idx}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                    {item}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Atmosphere Section */}
        {persona.atmosphere && (
          <div>
            <h4 className="font-medium text-primary mb-2">Atmosphere</h4>
            {persona.atmosphere.overall_vibe && (
              <p className="text-gray-700 dark:text-gray-300 mb-2 capitalize">{persona.atmosphere.overall_vibe}</p>
            )}
            {persona.atmosphere.descriptors && (
              <div className="flex flex-wrap gap-2">
                {persona.atmosphere.descriptors.map((item, idx) => (
                  <span key={`atm-${idx}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                    {item}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Use Cases Section */}
        {persona.use_cases && persona.use_cases.primary && (
          <div>
            <h4 className="font-medium text-primary mb-2">Perfect For</h4>
            <div className="space-y-1">
              {persona.use_cases.primary.map((item, idx) => (
                <div key={`use-${idx}`} className="flex items-center">
                  <span className="mr-2 text-primary">•</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Unique Attributes Section */}
        {persona.unique_attributes && (
          <div>
            <h4 className="font-medium text-primary mb-2">Standout Features</h4>
            <div className="space-y-1">
              {/* Display key selling points */}
              {persona.unique_attributes.key_selling_points && 
                persona.unique_attributes.key_selling_points.slice(0, 3).map((item, idx) => (
                  <div key={`attr-${idx}`} className="flex items-center">
                    <span className="mr-2 text-primary">✓</span>
                    <span>{item}</span>
                  </div>
                ))
              }
              
              {/* Display stand-out amenities if available */}
              {persona.unique_attributes.stand_out_amenities && 
                persona.unique_attributes.stand_out_amenities.slice(0, 2).map((item, idx) => (
                  <div key={`amenity-${idx}`} className="flex items-center">
                    <span className="mr-2 text-primary">✓</span>
                    <span>{item}</span>
                  </div>
                ))
              }
            </div>
          </div>
        )}
        
        {/* Market Position Section (new) */}
        {persona.market_position && (
          <div>
            <h4 className="font-medium text-primary mb-2">Experience Level</h4>
            {persona.market_position.property_class && (
              <p className="text-gray-700 dark:text-gray-300 mb-2 capitalize">
                <span className="font-medium">{persona.market_position.property_class}</span> accommodation
              </p>
            )}
            {persona.market_position.comparable_to && persona.market_position.comparable_to.length > 0 && (
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Similar to</p>
                <div className="flex flex-wrap gap-2">
                  {persona.market_position.comparable_to.map((item, idx) => (
                    <span key={`comp-${idx}`} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Footer with generation information */}
      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 flex justify-between items-center">
        <div>
          {persona.model && `Generated by ${persona.model}`} 
          {persona.generated_at && ` on ${new Date(persona.generated_at).toLocaleDateString()}`}
        </div>
        
        {/* Show creation method if available with color coding */}
        {persona.created_by && (
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