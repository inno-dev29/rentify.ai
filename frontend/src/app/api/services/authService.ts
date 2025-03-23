// authService.ts
// This service handles authentication-related operations

import apiClient from '../apiClient';
import sessionService from './sessionService';

// Interface for API response from /auth/login/
interface LoginResponse {
  key: string;  // Authentication token
  user?: any;
  [key: string]: any;
}

// Interface for the User object
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_staff?: boolean;
  is_active?: boolean;
  last_login?: string;
  date_joined?: string;
}

// Interface for login credentials
interface LoginCredentials {
  username: string;
  password: string;
}

// Interface for registration data
export interface RegistrationData {
  username: string;
  email: string;
  password1: string;
  password2: string;
  first_name?: string;
  last_name?: string;
}

// Interface for reset password data
export interface ResetPasswordData {
  uid: string;
  token: string;
  new_password1: string;
  new_password2: string;
}

// Variables to keep track of the last time we verified the token
// to avoid excessive verification calls
let lastVerificationTime = 0;
const VERIFICATION_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Handles logging in a user, storing their token in local storage
 */
const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  try {
    console.log(`Attempting to login user ${credentials.username}`);
    
    // First, clear any existing session
    sessionService.clearSession();
    
    // Make API request to login endpoint
    const response = await apiClient.post('/auth/login/', {
      username: credentials.username,
      password: credentials.password
    });
    
    console.log('Login successful');
    
    // Get the token from the response
    const token = response.key;
    
    // Now fetch the user data with the token
    const userData = await getCurrentUser(true);
    
    // Store token and user data in session
    sessionService.setSession(token, userData);
    
    return {
      key: token,
      user: userData
    };
  } catch (error: any) {
    console.error('Login failed:', error);
    
    // Check if this is a network error
    if (!error.status || error.message?.includes('fetch')) {
      const networkError = new Error('Network error connecting to authentication server');
      networkError.message = error.message || 'Network error connecting to authentication server';
      
      // Add a flag to identify this as a network error for the UI
      const customError: any = networkError;
      customError.isNetworkError = true;
      
      throw customError;
    }
    
    // Rethrow the error to be handled by the calling component
    throw error;
  }
};

/**
 * Verifies if the current token is valid
 * Returns true if valid, false otherwise
 */
const verifyToken = async (force = false): Promise<boolean> => {
  try {
    // Skip verification if we just checked recently, unless forced
    const now = Date.now();
    if (!force && (now - lastVerificationTime < VERIFICATION_INTERVAL)) {
      console.log('Skipping token verification, last verified recently');
      return sessionService.hasValidSession();
    }
    
    // If there's no session, return false immediately
    if (!sessionService.hasValidSession()) {
      console.log('No valid session found during token verification');
      return false;
    }
    
    // Verify token with the API directly
    const token = sessionService.getToken();
    if (!token) return false;
    
    // Make API request to verify token
    const response = await apiClient.post('/auth/token/verify/', { token });
    
    // Update the last verification time
    lastVerificationTime = now;
    
    return true;
  } catch (error) {
    console.error('Error verifying token:', error);
    
    // If verification fails, clear the session
    sessionService.clearSession();
    
    return false;
  }
};

/**
 * Logs out the current user
 */
const logout = async (): Promise<void> => {
  try {
    // Make API request to logout endpoint
    await apiClient.post('/auth/logout/', {});
    console.log('Logout API call successful');
  } catch (error) {
    console.error('Error during logout API call:', error);
    // Continue with local logout even if API call fails
  } finally {
    // Clear the session
    sessionService.clearSession();
    console.log('User logged out successfully');
  }
};

/**
 * Checks if a user is authenticated
 * Returns true if the user has a token stored
 */
const isAuthenticated = (): boolean => {
  return sessionService.hasValidSession();
};

/**
 * Fetches the current user data
 * First tries from sessionStorage, then from the API
 */
const getCurrentUser = async (forceRefresh = false): Promise<User | null> => {
  try {
    // If not forcing a refresh, return user data from session
    if (!forceRefresh) {
      const userData = sessionService.getUserData();
      if (userData) {
        return userData;
      }
    }
    
    // If no user data in session or forcing refresh, fetch from API
    if (sessionService.getToken()) {
      console.log('Fetching current user data from API');
      const response = await apiClient.get('/auth/user/');
      
      // Make sure we have a valid user response
      if (!response) {
        console.error('No response from user API');
        return null;
      }
      
      // Check if the response format is unexpected (e.g., just a detail message)
      if (response.detail && !response.username && !response.id) {
        console.warn('Unexpected user API response format:', response);
        // Try to fetch using a different endpoint as fallback
        try {
          const userProfile = await apiClient.get('/users/me/');
          if (userProfile && userProfile.id) {
            // Update the session with the user profile data
            const token = sessionService.getToken();
            if (token) {
              sessionService.setSession(token, userProfile);
            }
            return userProfile;
          }
        } catch (profileError) {
          console.error('Failed to fetch user profile as fallback:', profileError);
        }
        return null;
      }
      
      // Update the session with the latest user data
      const token = sessionService.getToken();
      if (token && response) {
        sessionService.setSession(token, response);
      }
      
      return response;
    }
    
    return null;
  } catch (error: any) {
    console.error('Error fetching current user:', error);
    
    // If we get an unauthorized error, clear the session
    if (error.status === 401) {
      sessionService.clearSession();
    }
    
    return null;
  }
};

/**
 * Registers a new user
 */
const register = async (data: RegistrationData): Promise<any> => {
  try {
    const response = await apiClient.post('/auth/registration/', data);
    return response;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

/**
 * Sends a password reset email
 */
const forgotPassword = async (email: string): Promise<any> => {
  try {
    const response = await apiClient.post('/auth/password/reset/', { email });
    return response;
  } catch (error) {
    console.error('Password reset request error:', error);
    throw error;
  }
};

/**
 * Resets a password with a token
 */
const resetPassword = async (data: ResetPasswordData): Promise<any> => {
  try {
    const response = await apiClient.post(`/auth/password/reset/confirm/`, data);
    return response;
  } catch (error) {
    console.error('Password reset confirmation error:', error);
    throw error;
  }
};

// Export all authentication functions
const authService = {
  login,
  logout,
  register,
  verifyToken,
  isAuthenticated,
  getCurrentUser,
  forgotPassword,
  resetPassword
};

export default authService; 