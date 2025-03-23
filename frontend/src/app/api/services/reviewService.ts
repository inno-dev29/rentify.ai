// reviewService.ts
// Service for review-related API calls

import apiClient, { API_BASE_URL, handleResponse } from '../apiClient';

// Define API endpoints
const REVIEWS_ENDPOINT = '/reviews/';

export const reviewService = {
  // Get all reviews for the current user
  getUserReviews: async () => {
    return apiClient.get(REVIEWS_ENDPOINT);
  },
  
  // Get reviews for a specific property
  getPropertyReviews: async (propertyId: number | string) => {
    return apiClient.get(`/properties/${propertyId}/reviews/`);
  },
  
  // Create a review for a booking
  createReview: async (reviewData: {
    booking_id: number | string;
    overall_rating: number;
    cleanliness_rating: number;
    accuracy_rating: number;
    location_rating: number;
    value_rating: number;
    communication_rating: number;
    comment: string;
  }) => {
    return apiClient.post(`/bookings/${reviewData.booking_id}/review/`, reviewData);
  },
  
  // Update a review
  updateReview: async (reviewId: number | string, reviewData: Partial<{
    overall_rating: number;
    cleanliness_rating: number;
    accuracy_rating: number;
    location_rating: number;
    value_rating: number;
    communication_rating: number;
    comment: string;
  }>) => {
    return apiClient.patch(`${REVIEWS_ENDPOINT}${reviewId}/`, reviewData);
  },
  
  // Delete a review
  deleteReview: async (reviewId: number | string) => {
    return apiClient.delete(`${REVIEWS_ENDPOINT}${reviewId}/`);
  },
  
  // Add a response to a review (for property owners)
  respondToReview: async (reviewId: number | string, response: string) => {
    return apiClient.patch(`${REVIEWS_ENDPOINT}${reviewId}/response/`, {
      leaser_response: response
    });
  },
  
  // Upload an image for a review
  uploadReviewImage: async (reviewId: number | string, imageData: FormData) => {
    return fetch(`${API_BASE_URL}${REVIEWS_ENDPOINT}${reviewId}/images/`, {
      method: 'POST',
      body: imageData,
      headers: {
        // Don't set Content-Type for FormData
        ...(typeof window !== 'undefined' && localStorage.getItem('auth_token') 
          ? { 'Authorization': `Token ${localStorage.getItem('auth_token')}` } 
          : {})
      }
    }).then(response => handleResponse(response));
  }
};

export default reviewService; 