// bookingService.ts
// Service for booking-related API calls

import axios from 'axios';
import apiClient from '../apiClient';
import authService from './authService';
import { getLogger, getToken } from '../utils/logger';

// Define API endpoints
const BOOKINGS_ENDPOINT = '/bookings/';

// Type definition for axios error
interface AxiosError {
  response?: {
    status: number;
    data: any;
  };
  request?: any;
  message: string;
}

// Function to check if an error is an axios error
const isAxiosError = (error: any): error is AxiosError => {
  return error && 
         error.isAxiosError === true && 
         (error.response !== undefined || error.request !== undefined);
};

// Interface for paginated response
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Interface for booking object
interface Booking {
  id: number;
  property: number | object;
  start_date: string;
  end_date: string;
  status: string;
  total_price: string | number;
  [key: string]: any; // Allow other properties
}

export const bookingService = {
  // Get all bookings for the current user
  getBookings: async () => {
    try {
      console.log('Fetching bookings from endpoint:', BOOKINGS_ENDPOINT);
      let retries = 0;
      let maxRetries = 2;
      let response;
      
      while (retries <= maxRetries) {
        try {
          response = await apiClient.get(BOOKINGS_ENDPOINT);
          break; // Exit the retry loop if successful
        } catch (error: any) {
          retries++;
          console.warn(`Booking fetch attempt ${retries} failed:`, error);
          
          if (retries > maxRetries) {
            // If we've exhausted retries, rethrow the error
            throw error;
          }
          
          // Wait before retrying (exponential backoff)
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retries - 1)));
          
          // If it seems like an auth issue, try to refresh the auth token
          if (error.status === 401 || error.status === 403) {
            try {
              const isLoggedIn = await authService.verifyToken(true);
              if (!isLoggedIn) {
                throw new Error('Authentication failed');
              }
            } catch (authError) {
              console.error('Authentication refresh failed:', authError);
              // Continue with retry anyway
            }
          }
        }
      }
      
      console.log('Raw bookings response:', response);
      
      // If we somehow don't have a response, return empty array
      if (!response) {
        console.warn('No response data from bookings endpoint, returning empty array');
        return [];
      }
      
      // Handle different response formats
      if (Array.isArray(response)) {
        // If response is already an array, return it directly
        console.log('Bookings response is an array with', response.length, 'items');
        return response;
      } else if (response && typeof response === 'object') {
        // Check if it's a paginated response
        if ('results' in response && Array.isArray(response.results)) {
          console.log('Bookings response is paginated with', response.results.length, 'items');
          return response.results;
        }
        
        // Check if it's an object containing bookings
        const possibleBookings = Object.values(response).filter(
          (item): item is Booking => 
            typeof item === 'object' && 
            item !== null && 
            'id' in item && 
            'property' in item
        );
        
        if (possibleBookings.length > 0) {
          console.log('Extracted bookings from object:', possibleBookings.length, 'items');
          return possibleBookings;
        }
      }
      
      // If we can't determine the format, return an empty array
      console.warn('Could not determine booking response format, returning empty array');
      return [];
    } catch (error: any) {
      console.error('Error fetching bookings:', error);
      
      // If there's an authentication error, try to get the user to log in again
      if (error.status === 401 || error.status === 403) {
        // Optionally trigger a login flow here or show a message
        console.warn('Authentication error fetching bookings. User may need to log in again.');
      }
      
      // Return empty array on error rather than throwing
      return [];
    }
  },
  
  // Get a single booking by ID
  getBooking: async (id: number | string) => {
    // Don't try to fetch a booking with an undefined ID
    if (id === undefined || id === null || id === 'undefined') {
      console.error('Invalid booking ID provided:', id);
      throw new Error('Invalid booking ID');
    }
    return apiClient.get(`${BOOKINGS_ENDPOINT}${id}/`);
  },
  
  // Create a new booking
  createBooking: async ({ propertyId, startDate, endDate, guestsCount, specialRequests }: {
    propertyId: number;
    startDate: string;
    endDate: string;
    guestsCount?: number;
    specialRequests?: string;
  }) => {
    try {
      // Pre-validation logging
      console.log('Attempting to create booking with data:', {
        propertyId,
        startDate,
        endDate,
        guestsCount,
        specialRequests
      });
      
      // Format the data for API submission
      const bookingData = {
        property: propertyId,
        start_date: startDate,
        end_date: endDate,
        guests_count: guestsCount || 1,
        special_requests: specialRequests || ''
      };
      
      console.log('Submitting booking data to API:', bookingData);
      
      // Submit the booking
      const response = await apiClient.post(BOOKINGS_ENDPOINT, bookingData);
      console.log('Booking creation successful:', response);
      return response;
    } catch (error: any) {
      console.error('Booking creation failed:', error);
      
      // Check for the specific error about booking own property
      if (error.errors && error.errors.detail === 'You cannot book your own property.') {
        console.error('User attempted to book their own property');
        throw new Error('You cannot book your own property');
      }
      
      // Handle other validation errors
      if (error.errors) {
        if (error.errors.start_date) {
          throw new Error(`Start date error: ${error.errors.start_date}`);
        }
        
        if (error.errors.end_date) {
          throw new Error(`End date error: ${error.errors.end_date}`);
        }
        
        if (error.errors.non_field_errors) {
          throw new Error(error.errors.non_field_errors);
        }
        
        // If we have errors but none of the above specific ones
        const errorMessages = Object.entries(error.errors)
          .map(([key, value]) => `${key}: ${value}`)
          .join('; ');
        
        if (errorMessages) {
          throw new Error(errorMessages);
        }
      }
      
      // If no structured errors are available
      throw error;
    }
  },
  
  // Cancel a booking
  cancelBooking: async (id: number | string) => {
    // Don't try to cancel a booking with an undefined ID
    if (id === undefined || id === null || id === 'undefined') {
      console.error('Invalid booking ID provided for cancellation:', id);
      throw new Error('Invalid booking ID');
    }
    return apiClient.patch(`${BOOKINGS_ENDPOINT}${id}/status/`, {
      status: 'cancelled'
    });
  },
  
  // Update booking status (for property owners)
  updateBookingStatus: async (id: number | string, status: 'confirmed' | 'rejected' | 'completed', reason?: string) => {
    // Don't try to update a booking with an undefined ID
    if (id === undefined || id === null || id === 'undefined') {
      console.error('Invalid booking ID provided for status update:', id);
      throw new Error('Invalid booking ID');
    }
    return apiClient.patch(`${BOOKINGS_ENDPOINT}${id}/status/`, {
      status,
      ...(reason && { cancellation_reason: reason })
    });
  },
  
  // Check property availability
  checkAvailability: async (propertyId: number | string, startDate: string, endDate: string) => {
    const logger = getLogger('bookingService.checkAvailability');
    
    logger.info(`Checking availability for property ${propertyId} from ${startDate} to ${endDate}`);
    
    try {
      // Try to get from the dedicated availability endpoint first
      const response = await apiClient.get(`/properties/${propertyId}/availability/?start_date=${startDate}&end_date=${endDate}`);
      logger.info('Successfully fetched from availability endpoint');
      return response;
    } catch (availabilityError: any) {
      // If endpoint returns an error, log it
      logger.warn(`Availability endpoint error: ${availabilityError.message || 'Unknown error'}`);
      
      if (availabilityError.status === 404) {
        logger.info('Availability endpoint not found (404). Using fallback method.');
      } else {
        logger.warn(`Availability endpoint returned error code: ${availabilityError.status || 'Unknown'}`);
      }
      
      // Fallback method: Calculate availability from existing bookings
      // This implementation will work even if the main availability endpoint fails
      
      // Use the new property bookings endpoint
      try {
        const bookingsResponse = await apiClient.get(`/properties/${propertyId}/bookings/`);
        const bookings = Array.isArray(bookingsResponse) ? bookingsResponse : 
                        (bookingsResponse?.results || bookingsResponse || []);
        
        if (Array.isArray(bookings) && bookings.length > 0) {
          logger.info(`Found ${bookings.length} bookings for property ${propertyId}`);
          
          // Extract booked dates from existing bookings
          const bookedDates = new Set<string>();
          
          bookings.forEach(booking => {
            if (booking.status !== 'cancelled') {
              const start = new Date(booking.start_date);
              const end = new Date(booking.end_date);
              
              // For each day in the booking range
              for (let day = new Date(start); day <= end; day.setDate(day.getDate() + 1)) {
                bookedDates.add(day.toISOString().split('T')[0]);
              }
            }
          });
          
          // Return in the same format as the expected API response
          return {
            property_id: propertyId,
            unavailable_dates: Array.from(bookedDates),
            available: bookedDates.size === 0,
            start_date: startDate,
            end_date: endDate
          };
        }
        
        logger.info(`No bookings found for property ${propertyId}`);
        return {
          property_id: propertyId,
          unavailable_dates: [],
          available: true,
          start_date: startDate,
          end_date: endDate
        };
        
      } catch (bookingsError: any) {
        logger.error(`Failed to fetch property bookings: ${bookingsError.message || 'Unknown error'}`);
        logger.error(`Property bookings endpoint error code: ${bookingsError.status || 'Unknown'}`);
        
        // Return empty availability as a last resort
        return {
          property_id: propertyId,
          unavailable_dates: [],
          available: true,
          start_date: startDate,
          end_date: endDate
        };
      }
    }
  }
};

export default bookingService; 