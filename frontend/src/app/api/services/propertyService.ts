// propertyService.ts
// Service for property-related API calls

import apiClient, { API_BASE_URL, handleResponse } from '../apiClient';
import { Property, PropertyImage, Amenity } from '@/types/property';

// Define API endpoints
const PROPERTIES_ENDPOINT = '/properties/';
const AMENITIES_ENDPOINT = '/properties/amenities/';
const BOOKINGS_ENDPOINT = '/bookings/';

export type Booking = {
  id: number;
  property: number;
  start_date: string;
  end_date: string;
  total_price: string;
  status: 'pending' | 'confirmed' | 'cancelled';
  created_at?: string;
};

export type PropertyFilterParams = {
  type?: string;
  location?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  min_bathrooms?: number;
  min_guests?: number;
  status?: 'active' | 'inactive' | 'pending' | 'archived';
  amenities?: string; // Comma-separated list of amenity IDs
};

export const propertyService = {
  // Get all properties with optional filtering
  getProperties: async (filters?: PropertyFilterParams) => {
    let queryParams = '';
    
    if (filters) {
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
      
      queryParams = params.toString() ? `?${params.toString()}` : '';
    }
    
    const response = await apiClient.get(`${PROPERTIES_ENDPOINT}${queryParams}`);
    return response;
  },
  
  // Get a single property by ID
  getProperty: async (id: number) => {
    return apiClient.get(`${PROPERTIES_ENDPOINT}${id}/`);
  },
  
  // Create a new property (requires authentication)
  createProperty: async (propertyData: Omit<Property, 'id'>) => {
    return apiClient.post(PROPERTIES_ENDPOINT, propertyData);
  },
  
  // Update an existing property (requires authentication and ownership)
  updateProperty: async (id: number, propertyData: Partial<Property>) => {
    return apiClient.patch(`${PROPERTIES_ENDPOINT}${id}/`, propertyData);
  },
  
  // Delete a property (requires authentication and ownership)
  deleteProperty: async (id: number) => {
    return apiClient.delete(`${PROPERTIES_ENDPOINT}${id}/`);
  },
  
  // Get all amenities
  getAmenities: async () => {
    return apiClient.get(AMENITIES_ENDPOINT);
  },
  
  // Get images for a property
  getPropertyImages: async (propertyId: number | string) => {
    return apiClient.get(`${PROPERTIES_ENDPOINT}${propertyId}/images/`);
  },
  
  // Upload a property image
  uploadPropertyImage: async (propertyId: number | string, imageData: FormData) => {
    return fetch(`${API_BASE_URL}${PROPERTIES_ENDPOINT}${propertyId}/images/`, {
      method: 'POST',
      body: imageData,
      headers: {
        // Don't set Content-Type for FormData, browser will set it with correct boundary
        // Include auth token if available
        ...(typeof window !== 'undefined' && localStorage.getItem('auth_token') 
          ? { 'Authorization': `Token ${localStorage.getItem('auth_token')}` } 
          : {})
      }
    }).then(response => handleResponse(response));
  },
  
  // Delete a property image
  deletePropertyImage: async (propertyId: number | string, imageId: number | string) => {
    return apiClient.delete(`${PROPERTIES_ENDPOINT}${propertyId}/images/${imageId}/`);
  },
  
  // Get property summary from LLM service
  getPropertySummary: async (propertyId: number | string) => {
    return apiClient.get(`/llm/properties/${propertyId}/summary/`);
  },
  
  // Check property availability
  checkAvailability: async (propertyId: number | string, startDate: string, endDate: string) => {
    return apiClient.get(`/properties/${propertyId}/availability/?start_date=${startDate}&end_date=${endDate}`);
  },
  
  // Get all bookings for the authenticated user
  getUserBookings: async () => {
    return apiClient.get(`${BOOKINGS_ENDPOINT}`);
  },
  
  // Create a new booking (requires authentication)
  createBooking: async (bookingData: { 
    property: number; 
    start_date: string; 
    end_date: string;
  }) => {
    return apiClient.post(BOOKINGS_ENDPOINT, bookingData);
  },
  
  // Cancel a booking (requires authentication and ownership)
  cancelBooking: async (id: number) => {
    return apiClient.patch(`${BOOKINGS_ENDPOINT}${id}/`, { status: 'cancelled' });
  }
};

export default propertyService; 