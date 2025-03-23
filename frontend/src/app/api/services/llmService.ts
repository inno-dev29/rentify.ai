// llmService.ts
// Service for LLM-related API calls

import apiClient from '@/app/api/apiClient';
import { 
  PropertySummary, 
  PropertyPersona, 
  UserRecommendations,
  UserPersona,
  PropertyRecommendation,
  ConversationalRecommendations
} from '@/types/property';

// Define API endpoints
const LLM_ENDPOINT = '/llm/';
// Define Next.js API routes for proxying requests
const NEXTJS_API_ENDPOINT = '/api/llm/';

/**
 * Service for interacting with LLM-related endpoints.
 */
export const llmService = {
  // Get a property summary
  getPropertySummary: async (propertyId: number | string): Promise<PropertySummary> => {
    try {
      // Use Next.js API route instead of direct backend call
      const response = await fetch(`${NEXTJS_API_ENDPOINT}properties/${propertyId}/summary/`);
      
      if (!response.ok) {
        throw new Error(`Error fetching property summary: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Property summary data from Next.js API route:', data);
      
      // Case 1: Direct string response
      if (typeof data === 'string') {
        console.log('Received string response:', data);
        return {
          property_id: Number(propertyId),
          summary: data,
          highlights: [],
          generated_at: new Date().toISOString(),
          created_by: 'api'
        };
      }
      
      // Case 2: Response with summary as direct property
      if (data && typeof data.summary === 'string') {
        console.log('Received object with string summary property:', data);
        return {
          property_id: Number(propertyId),
          summary: data.summary,
          highlights: data.highlights || [],
          generated_at: data.generated_at || data.created_at || new Date().toISOString(),
          created_by: data.created_by || 'api',
          model: data.model || data.generate_version
        };
      }
      
      // Case 3: Response is the summary object itself
      if (data && typeof data === 'object') {
        console.log('Received summary object:', data);
        // Create a base summary object with required properties
        const summaryObj: PropertySummary = {
          property_id: Number(propertyId),
          summary: typeof data.summary_text === 'string' ? data.summary_text : 
                  (typeof data.summary === 'string' ? data.summary : 
                  'No summary available'),
          highlights: Array.isArray(data.highlights) ? data.highlights : [],
          generated_at: data.generated_at || data.created_at || data.updated_at || new Date().toISOString(),
          created_by: data.created_by || 'api',
          model: data.model || data.generate_version
        };
        
        return summaryObj;
      }
      
      // Fallback: If we can't determine the structure, create a default summary
      console.warn('Unrecognized response format:', data);
      return {
        property_id: Number(propertyId),
        summary: 'Summary unavailable. Please try again later.',
        highlights: [],
        generated_at: new Date().toISOString(),
        created_by: 'fallback'
      };
    } catch (error) {
      console.error('Error in getPropertySummary:', error);
      throw error;
    }
  },
  
  // Get a user persona
  getUserPersona: async (userId?: number | string): Promise<UserPersona> => {
    // If userId is not provided, use 'me' to get the current user's persona
    const endpoint = userId ? `users/${userId}/persona/` : 'users/me/persona/';
    const response = await apiClient.get(`${LLM_ENDPOINT}${endpoint}`);
    return response.persona;
  },
  
  /**
   * Refreshes a user's persona by deleting the existing one and generating a new one.
   * This is useful after updating user preferences to get an updated persona.
   * 
   * @param userId - The ID of the user to refresh the persona for
   * @returns Promise resolving to the new user persona
   */
  refreshUserPersona: async (userId: number | string): Promise<UserPersona> => {
    try {
      console.log(`Refreshing user persona for user ID: ${userId}`);
      const endpoint = `users/${userId}/persona/`;
      const response = await apiClient.delete(`${LLM_ENDPOINT}${endpoint}`);
      console.log('Refresh persona response:', response);
      
      // If response contains persona, return it
      if (response && response.persona) {
        return response.persona;
      }
      
      // If we just get a success message, return a placeholder
      return {
        user_id: Number(userId),
        preferences: {},
        interests: [],
        generated_at: new Date().toISOString(),
        travel_habits: {
          typical_group_size: '',
          typical_stay_length: '',
          booking_frequency: '',
          planning_style: ''
        }
      };
    } catch (error) {
      console.error('Error in refreshUserPersona:', error);
      throw error; // Re-throw the error for the component to handle
    }
  },
  
  /**
   * Fetches the property persona for a given property ID.
   * 
   * @param propertyId - The ID of the property to get the persona for
   * @returns Promise resolving to the property persona
   */
  async getPropertyPersona(propertyId: number | string): Promise<PropertyPersona> {
    try {
      const response = await apiClient.get(`${LLM_ENDPOINT}properties/${propertyId}/persona/`);
      
      // Handle the response structure from the backend
      // The backend returns { persona: {...}, created_at: "...", updated_at: "..." }
      const propertyPersona = response.persona;
      
      // Add generated_at and model fields if they don't exist
      if (!propertyPersona.generated_at && response.created_at) {
        propertyPersona.generated_at = response.created_at;
      }
      
      if (!propertyPersona.model && response.persona.generate_version) {
        propertyPersona.model = response.persona.generate_version;
      }
      
      // Add property_id if it doesn't exist
      if (!propertyPersona.property_id) {
        propertyPersona.property_id = Number(propertyId);
      }
      
      return propertyPersona;
    } catch (error) {
      console.error('Error in getPropertyPersona:', error);
      throw error;
    }
  },
  
  /**
   * Gets personalized property recommendations for the current user.
   * 
   * @returns Promise resolving to user recommendations
   */
  async getRecommendations(): Promise<UserRecommendations> {
    try {
      const response = await apiClient.get(`${LLM_ENDPOINT}users/me/recommendations/`);
      return response;
    } catch (error: any) {
      console.error('Error in getRecommendations:', error);
      
      // For unauthorized errors, return a fallback empty recommendations object
      if (error.status === 401) {
        console.log('User not authenticated, returning empty recommendations');
        return {
          recommendations: [],
          generated_at: new Date().toISOString(),
          error_message: 'Please log in to see personalized recommendations'
        };
      }
      
      // For server errors, return a generic error message
      if (error.status >= 500) {
        console.log('Server error, returning empty recommendations');
        return {
          recommendations: [],
          generated_at: new Date().toISOString(),
          error_message: 'The recommendation service is temporarily unavailable'
        };
      }
      
      // For all other errors, return a generic recommendations object
      return {
        recommendations: [],
        generated_at: new Date().toISOString(),
        error_message: error.message || 'Failed to load recommendations'
      };
    }
  },
  
  /**
   * Gets personalized property recommendations for a specific user.
   * 
   * @param userId - The ID of the user to get recommendations for
   * @returns Promise resolving to user recommendations
   */
  async getUserRecommendations(userId: number | string): Promise<UserRecommendations> {
    try {
      const response = await apiClient.get(`${LLM_ENDPOINT}users/${userId}/recommendations/`);
      return response;
    } catch (error: any) {
      console.error('Error in getUserRecommendations:', error);
      
      // For unauthorized or forbidden errors, return a fallback
      if (error.status === 401 || error.status === 403) {
        console.log(`User ${userId} recommendations access denied, returning empty recommendations`);
        return {
          recommendations: [],
          generated_at: new Date().toISOString(),
          error_message: 'You do not have permission to view these recommendations'
        };
      }
      
      // For server errors, return a generic error message
      if (error.status >= 500) {
        console.log('Server error, returning empty recommendations');
        return {
          recommendations: [],
          generated_at: new Date().toISOString(),
          error_message: 'The recommendation service is temporarily unavailable'
        };
      }
      
      // For all other errors, return a generic recommendations object
      return {
        recommendations: [],
        generated_at: new Date().toISOString(),
        error_message: error.message || 'Failed to load recommendations'
      };
    }
  },
  
  /**
   * Gets conversational property recommendations for the current user.
   * Utilizes the LangChain-powered recommendations API.
   * 
   * @param query - Optional natural language query to refine recommendations
   * @returns Promise resolving to conversational recommendations
   */
  async getConversationalRecommendations(query?: string): Promise<ConversationalRecommendations> {
    try {
      const endpoint = `${LLM_ENDPOINT}recommendations/conversational/`;
      const url = query ? `${endpoint}?query=${encodeURIComponent(query)}` : endpoint;
      const response = await apiClient.get(url);
      return response;
    } catch (error: any) {
      console.error('Error in getConversationalRecommendations:', error);
      
      // For unauthorized errors, return a fallback empty recommendations object
      if (error.status === 401) {
        return {
          personalized_explanation: '',
          properties: [],
          follow_up_questions: [],
          error_message: 'Please log in to see personalized recommendations'
        };
      }
      
      // For server errors, return a generic error message
      if (error.status >= 500) {
        return {
          personalized_explanation: '',
          properties: [],
          follow_up_questions: [],
          error_message: 'The recommendation service is temporarily unavailable'
        };
      }
      
      // For all other errors, return a generic response
      return {
        personalized_explanation: '',
        properties: [],
        follow_up_questions: [],
        error_message: error.message || 'Failed to load recommendations'
      };
    }
  },
  
  /**
   * Refines conversational recommendations based on user feedback.
   * 
   * @param feedback - User feedback or follow-up question
   * @returns Promise resolving to refined conversational recommendations
   */
  async refineConversationalRecommendations(feedback: string): Promise<ConversationalRecommendations> {
    try {
      const response = await apiClient.post(`${LLM_ENDPOINT}recommendations/conversational/`, {
        feedback
      });
      return response;
    } catch (error: any) {
      console.error('Error in refineConversationalRecommendations:', error);
      
      // For unauthorized errors
      if (error.status === 401) {
        return {
          personalized_explanation: '',
          properties: [],
          follow_up_questions: [],
          error_message: 'Please log in to see personalized recommendations'
        };
      }
      
      // For all other errors
      return {
        personalized_explanation: '',
        properties: [],
        follow_up_questions: [],
        error_message: error.message || 'Failed to refine recommendations'
      };
    }
  },
  
  /**
   * Clears the conversation history/memory for the conversational recommendations.
   * 
   * @returns Promise resolving to a confirmation message
   */
  async clearConversationHistory(): Promise<{ message: string }> {
    try {
      const response = await apiClient.delete(`${LLM_ENDPOINT}recommendations/conversational/`);
      return { message: 'Conversation history cleared successfully' };
    } catch (error: any) {
      console.error('Error in clearConversationHistory:', error);
      throw error;
    }
  },
  
  // Get cache statistics (admin only)
  getCacheStats: async (): Promise<any> => {
    return apiClient.get(`${LLM_ENDPOINT}cache/stats/`);
  },
  
  // Clear cache (admin only)
  clearCache: async (options?: { days?: number, hours?: number }): Promise<any> => {
    let endpoint = `${LLM_ENDPOINT}cache/clear/`;
    if (options) {
      const params = new URLSearchParams();
      if (options.days) params.append('days', options.days.toString());
      if (options.hours) params.append('hours', options.hours.toString());
      if (params.toString()) endpoint += `?${params.toString()}`;
    }
    return apiClient.post(endpoint, {});
  },
  
  // Regenerate all property summaries (admin only)
  regenerateSummaries: async (): Promise<any> => {
    return apiClient.post(`${LLM_ENDPOINT}properties/regenerate-summaries/`, {});
  },
  
  // Generate a property description
  generatePropertyDescription: async (propertyId: number | string): Promise<any> => {
    return apiClient.post(`${LLM_ENDPOINT}properties/${propertyId}/generate-description/`, {});
  },
  
  // Get LLM provider info
  getProviderInfo: async (): Promise<any> => {
    return apiClient.get(`${LLM_ENDPOINT}info/`);
  },

  /**
   * Generates a personalized response for a user based on their question about a property.
   * 
   * @param propertyId - The ID of the property the question is about
   * @param question - The user's question about the property
   * @returns Promise resolving to the AI-generated response
   */
  async generatePropertyResponse(propertyId: number | string, question: string): Promise<{ response: string }> {
    try {
      const response = await apiClient.post(
        `${LLM_ENDPOINT}properties/${propertyId}/question/`, 
        { question }
      );
      return response;
    } catch (error) {
      console.error('Error in generatePropertyResponse:', error);
      throw error;
    }
  }
};

export default llmService; 