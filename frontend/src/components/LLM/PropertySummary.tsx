'use client';

import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import { PropertySummary as PropertySummaryType } from '@/types/property';

interface PropertySummaryProps {
  propertyId: number | string;
  className?: string;
}

export default function PropertySummary({ propertyId, className = '' }: PropertySummaryProps) {
  const [summary, setSummary] = useState<PropertySummaryType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFallbackData, setIsFallbackData] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
  
  // For debugging
  useEffect(() => {
    console.log(`[PropertySummary] Using API URL: ${API_BASE_URL}`);
  }, [API_BASE_URL]);

  useEffect(() => {
    async function fetchSummary() {
      console.log(`[PropertySummary] Fetching summary for property ${propertyId}...`);
      try {
        setLoading(true);
        setIsFallbackData(false);
        
        // Fetch directly from the backend API instead of the Next.js API route
        const apiUrl = `${API_BASE_URL}/llm/properties/${propertyId}/summary/`;
        console.log(`[PropertySummary] Making API request to: ${apiUrl}`);
        
        // Add credentials and CORS headers
        const response = await fetch(apiUrl, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          mode: 'cors', // Explicitly set CORS mode
          credentials: 'include',
        });
        
        console.log(`[PropertySummary] API response status: ${response.status}`);
        
        if (!response.ok) {
          throw new Error(`Error fetching property summary: ${response.statusText}`);
        }
        
        // Try-catch block to help debug parsing issues
        let data;
        try {
          const text = await response.text();
          console.log(`[PropertySummary] Raw response text:`, text.substring(0, 150) + '...');
          data = JSON.parse(text);
        } catch (parseError: unknown) {
          console.error(`[PropertySummary] JSON parsing error:`, parseError);
          const errorMessage = parseError instanceof Error ? parseError.message : 'Unknown JSON parsing error';
          throw new Error(`Failed to parse API response: ${errorMessage}`);
        }
        
        console.log('[PropertySummary] Received data:', JSON.stringify(data, null, 2));
        
        // Set fallback state based on data source
        if (data.created_by === 'fallback') {
          console.log('[PropertySummary] Detected fallback data by created_by field');
          setIsFallbackData(true);
        } else {
          // For backward compatibility with responses that might still have the marker
          const hasFallbackMarker = data.summary?.includes('fallback data') || 
                                   data.highlights?.some(
                                     (highlight: string) => highlight.includes('FALLBACK DATA - API ERROR')
                                   );
          
          if (hasFallbackMarker) {
            console.log('[PropertySummary] Detected fallback data by fallback marker');
            // Filter out the fallback marker from highlights if present
            if (data.highlights) {
              data.highlights = data.highlights.filter(
                (highlight: string) => !highlight.includes('FALLBACK DATA - API ERROR')
              );
            }
            setIsFallbackData(true);
          }
        }
        
        setSummary(data);
        setError(null);
      } catch (err) {
        console.error('[PropertySummary] Error fetching property summary:', err);
        setError('Unable to load AI-generated summary');
      } finally {
        setLoading(false);
      }
    }
    
    if (propertyId) {
      fetchSummary();
    }
  }, [propertyId, API_BASE_URL]);

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-4 bg-gray-200 dark:bg-gray-300 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-300 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-300 rounded w-5/6 mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-300 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-300 rounded w-2/3"></div>
      </div>
    );
  }

  if (error || !summary) {
    console.log('[PropertySummary] Not rendering due to error or missing summary:', { error, hasSummary: !!summary });
    return null; // Don't show any error to user, just don't display the summary
  }

  console.log('[PropertySummary] Rendering summary:', summary);

  // Helper function to determine badge color based on creation method
  const getCreationMethodBadgeClass = () => {
    if (!summary.created_by) return "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400";
    
    switch (summary.created_by) {
      case "claude":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case "claude-fixed":
        // Same styling as normal claude responses - this is not a fallback
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case "regex-extraction":
        return "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400";
      case "fallback":
        return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300";
      default:
        return "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400";
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 my-6 ${className}`}>
      {isFallbackData && (
        <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 mb-4">
          <div className="flex items-center text-amber-600 dark:text-amber-500 mb-1">
            <AlertCircle className="w-4 h-4 mr-2" />
            <span className="font-medium">Temporary Data</span>
          </div>
          <p className="text-sm text-amber-700 dark:text-amber-400">
            We're currently experiencing issues generating a custom AI summary for this property. 
            We've provided basic information while we resolve this issue.
          </p>
        </div>
      )}
      
      <h3 className="text-lg font-semibold mb-3">AI-Generated Property Summary</h3>
      <p className="text-gray-700 dark:text-gray-300 mb-4">{summary.summary}</p>
      
      {summary.highlights && summary.highlights.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium mb-2">Property Highlights</h4>
          <ul className="space-y-1">
            {summary.highlights.map((highlight, index) => (
              <li key={index} className="flex items-start">
                <span className="text-primary mr-2">✓</span>
                <span>{highlight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        {summary.model && (
          <div>
            Generated by {summary.model} on {new Date(summary.generated_at).toLocaleDateString()}
          </div>
        )}
        
        {summary.created_by && (
          <div className={`px-2 py-0.5 rounded ${getCreationMethodBadgeClass()}`}>
            {summary.created_by}
          </div>
        )}
      </div>
    </div>
  );
} 