// apiClient.ts
// Base client for API requests

// Define the API base URL based on environment
// This should point to the Django backend server
export const API_BASE_URL = typeof window !== 'undefined' 
  ? 'http://localhost:8005/api'  // Use port 8005 for local development
  : 'http://localhost:8005/api';  // Use same port for server-side rendering

import sessionService from './services/sessionService';

// Maximum number of retry attempts
const MAX_RETRIES = 1;

// Function to get CSRF token from cookies
const getCSRFToken = (): string | null => {
  if (typeof document === 'undefined') return null;
  
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i].trim();
    if (cookie.startsWith('csrftoken=')) {
      return cookie.substring('csrftoken='.length, cookie.length);
    }
  }
  return null;
};

// Function to refresh authentication
const refreshAuth = async (): Promise<boolean> => {
  console.log('Attempting to refresh authentication token...');
  
  // Clear old token
  if (typeof window !== 'undefined') {
    sessionService.clearSession();
  }
  
  try {
    // This should be replaced with your actual token refresh logic
    // For example, calling a refresh token endpoint
    // For now, we'll just return false to indicate we couldn't refresh
    return false;
  } catch (error) {
    console.error('Failed to refresh authentication:', error);
    return false;
  }
};

// Utility function to handle fetch responses
export const handleResponse = async (response: Response) => {
  console.log('Received API response:', { 
    status: response.status, 
    statusText: response.statusText,
    url: response.url
  });
  
  const contentType = response.headers.get('content-type');
  
  // Handle different response types
  if (contentType && contentType.includes('application/json')) {
    try {
      const data = await response.json();
      console.log('Response data:', data);
      
      if (!response.ok) {
        // Handle API errors
        const error = {
          status: response.status,
          message: data.detail || getDefaultErrorMessage(response.status),
          errors: data.errors || {}
        };
        console.error('API error:', error);
        throw error;
      }
      
      return data;
    } catch (error) {
      console.error('Error parsing JSON response:', error);
      throw new Error(`Failed to parse JSON response: ${error}`);
    }
  }
  
  // For non-JSON responses
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Non-JSON error response:', errorText);
    
    // Create a structured error object even for non-JSON responses
    const error = {
      status: response.status,
      message: errorText || getDefaultErrorMessage(response.status),
      errors: {}
    };
    throw error;
  }
  
  return response.text();
};

// Process API errors properly
const processApiError = async (response: Response) => {
  try {
    // Clone the response so we can log it and also read it as json
    const clonedResponse = response.clone();
    
    try {
      // Try to parse as JSON
      const errorData = await response.json();
      console.log('API error response:', {
        status: response.status,
        statusText: response.statusText,
        data: errorData,
      });
      
      // Structure the error nicely
      const error: any = new Error(errorData.detail || errorData.non_field_errors?.[0] || 'API request failed');
      error.status = response.status;
      error.statusText = response.statusText;
      error.errors = errorData;
      
      return Promise.reject(error);
    } catch (parseError: unknown) {
      // If it's not valid JSON, try to get text
      console.warn('Failed to parse error response as JSON:', parseError);
      const textResponse = await clonedResponse.text();
      
      const error: any = new Error(`API request failed: ${response.statusText}`);
      error.status = response.status;
      error.statusText = response.statusText;
      error.responseText = textResponse;
      
      return Promise.reject(error);
    }
  } catch (finalError) {
    // If all else fails
    const error: any = new Error('Failed to process API error response');
    error.status = response.status;
    error.statusText = response.statusText;
    error.originalError = finalError;
    
    return Promise.reject(error);
  }
};

// Main fetch function with authentication
const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<any> => {
  // Get token from session service
  const token = typeof window !== 'undefined' ? sessionService.getToken() : null;
  const csrfToken = getCSRFToken();
  
  if (!token) {
    console.warn('No authentication token found in session');
  }
  
  if (!csrfToken) {
    console.warn('No CSRF token found in cookies');
  }
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(token ? { 'Authorization': `Token ${token}` } : {}),
    ...(csrfToken && (options.method === 'POST' || options.method === 'PUT' || options.method === 'PATCH' || options.method === 'DELETE') 
      ? { 'X-CSRFToken': csrfToken } 
      : {}),
    ...(options.headers || {})
  };
  
  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include',  // Include credentials (cookies) in the request
    mode: 'cors',            // Set CORS mode explicitly
  };
  
  console.log(`Making API request to: ${API_BASE_URL}${url}`, config);
  
  try {
    // Make the request
    const response = await fetch(`${API_BASE_URL}${url}`, config);
    
    console.log('Received API response:', {
      status: response.status,
      statusText: response.statusText,
      url: response.url
    });
    
    // Check for auth-related errors
    if (response.status === 401) {
      console.warn('Received 401 Unauthorized response');
      
      // Clear current session as it's invalid
      sessionService.clearSession();
      
      // You could try to refresh the token here if you have refresh token functionality
      // For now, just continue with the error handling
    }
    
    // Handle successful response
    if (response.ok) {
      // Check if there's a response body by looking at content-length
      const contentLength = response.headers.get('content-length');
      if (contentLength === '0') {
        return null; // Return null for empty responses
      }
      
      // Try to parse as JSON
      try {
        const data = await response.json();
        console.log('Response data:', data);
        return data;
      } catch (error) {
        console.warn('Response is not JSON:', error);
        // If it's not JSON, return text content
        const text = await response.text();
        return text;
      }
    }
    
    // Handle error response
    return processApiError(response);
  } catch (error) {
    console.error(`API request failed:`, error);
    throw error;
  }
};

// API client with methods for different HTTP verbs
const apiClient = {
  get: (url: string, options: RequestInit = {}) => {
    return fetchWithAuth(url, { ...options, method: 'GET' });
  },
  
  post: (url: string, data: any, options: RequestInit = {}) => {
    return fetchWithAuth(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  put: (url: string, data: any, options: RequestInit = {}) => {
    return fetchWithAuth(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  patch: (url: string, data: any, options: RequestInit = {}) => {
    return fetchWithAuth(url, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },
  
  delete: (url: string, options: RequestInit = {}) => {
    return fetchWithAuth(url, { ...options, method: 'DELETE' });
  }
};

// Helper function to get default error messages based on status codes
const getDefaultErrorMessage = (status: number): string => {
  switch (status) {
    case 400:
      return 'Bad Request: The server could not understand your request.';
    case 401:
      return 'Unauthorized: You need to be logged in to access this resource.';
    case 403:
      return 'Forbidden: You do not have permission to access this resource.';
    case 404:
      return 'Not Found: The requested resource was not found.';
    case 500:
      return 'Internal Server Error: Something went wrong on our servers.';
    default:
      return `Error ${status}: An unexpected error occurred.`;
  }
};

export default apiClient; 