// sessionService.ts
// Service for managing user sessions and authentication state

import apiClient from '../apiClient';

// Define type for session data
interface SessionData {
  token: string;
  user?: any;
  expiresAt?: number;
}

// Set the session timeout (15 minutes in milliseconds)
const SESSION_TIMEOUT = 15 * 60 * 1000; // 15 minutes

/**
 * Session Service - Provides methods for managing user session
 * This abstracts token storage and session management away from the auth context
 */
export const sessionService = {
  /**
   * Set the current session
   * @param token Authentication token
   * @param userData User data to store
   */
  setSession(token: string, userData: any): void {
    // Calculate expiry time
    const expiresAt = Date.now() + SESSION_TIMEOUT;
    
    // Store session data
    const sessionData: SessionData = {
      token,
      user: userData,
      expiresAt
    };
    
    // Save token and user data
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_data', JSON.stringify(userData));
    localStorage.setItem('session_expires', expiresAt.toString());
    
    // Dispatch storage event for cross-tab synchronization
    this.notifySessionChange('session_updated');
    
    console.log('Session created:', { token: '***', expiresAt: new Date(expiresAt).toISOString() });
  },
  
  /**
   * Clear the current session
   */
  clearSession(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('username');
    localStorage.removeItem('session_expires');
    
    // Dispatch storage event for cross-tab synchronization
    this.notifySessionChange('session_cleared');
    
    console.log('Session cleared');
  },
  
  /**
   * Check if a session exists and is valid
   * @returns Boolean indicating if the session is valid
   */
  hasValidSession(): boolean {
    // Check if token exists
    const token = localStorage.getItem('auth_token');
    if (!token) return false;
    
    // Check if session has expired
    const expiresAtStr = localStorage.getItem('session_expires');
    if (expiresAtStr) {
      const expiresAt = parseInt(expiresAtStr, 10);
      if (Date.now() > expiresAt) {
        // Session has expired
        this.clearSession();
        return false;
      }
    }
    
    return true;
  },
  
  /**
   * Get the current user data
   * @returns User data object or null if no session exists
   */
  getUserData(): any | null {
    if (!this.hasValidSession()) return null;
    
    const userData = localStorage.getItem('user_data');
    if (!userData) return null;
    
    try {
      return JSON.parse(userData);
    } catch (e) {
      console.error('Error parsing user data:', e);
      return null;
    }
  },
  
  /**
   * Get the current authentication token
   * @returns Token string or null if no session exists
   */
  getToken(): string | null {
    if (!this.hasValidSession()) return null;
    return localStorage.getItem('auth_token');
  },
  
  /**
   * Extend the current session timeout
   */
  extendSession(): void {
    const token = localStorage.getItem('auth_token');
    if (!token) return;
    
    const expiresAt = Date.now() + SESSION_TIMEOUT;
    localStorage.setItem('session_expires', expiresAt.toString());
    
    console.log('Session extended until:', new Date(expiresAt).toISOString());
  },
  
  /**
   * Verify session with the backend
   * @returns Promise resolving to boolean indicating if token is valid
   */
  async verifySession(): Promise<boolean> {
    if (!this.hasValidSession()) return false;
    
    try {
      // Verify token with backend directly
      const token = this.getToken();
      if (!token) return false;
      
      // Use apiClient to verify token
      const response = await apiClient.post('/auth/token/verify/', { token });
      
      // If we get here without an error, the token is valid
      this.extendSession();
      
      // If the response includes user data, update the session
      if (response && response.user) {
        // Update user data in local storage
        localStorage.setItem('user_data', JSON.stringify(response.user));
      }
      
      return true;
    } catch (error: any) {
      console.error('Error verifying session:', error);
      
      // Only clear the session if we get an authentication error (401)
      // or if the token is explicitly invalid
      if (error.status === 401 || 
          (error.errors && error.errors.detail === 'Invalid token.')) {
        this.clearSession();
        return false;
      }
      
      // For other errors (like network issues or 404), don't immediately invalidate the session
      // This prevents accidentally logging users out if there are temporary API issues
      if (error.status === 404) {
        console.warn('Token verification endpoint not found. Check backend configuration.');
        // Still extend the session since we couldn't verify it's invalid
        this.extendSession();
        return true;
      }
      
      // Default behavior - assume session is still valid if we can't verify otherwise
      return true;
    }
  },
  
  /**
   * Notify all tabs of session changes
   * This uses a custom event as localStorage events only fire on other tabs
   */
  notifySessionChange(action: 'session_updated' | 'session_cleared'): void {
    if (typeof window === 'undefined') return;
    
    // Use storage event for cross-tab communication
    // We set and immediately remove a value to trigger storage events
    localStorage.setItem('session_sync', action);
    localStorage.removeItem('session_sync');
    
    // Also dispatch a custom event for the current tab
    window.dispatchEvent(new CustomEvent('session_change', { detail: { action } }));
  },
  
  /**
   * Initialize the session service (call this once at app startup)
   */
  init(): void {
    if (typeof window === 'undefined') return;
    
    // Check for expired sessions on startup
    if (this.hasValidSession()) {
      this.extendSession();
    }
    
    // Set up interval to periodically check session validity
    setInterval(() => {
      if (this.hasValidSession()) {
        this.verifySession();
      }
    }, 5 * 60 * 1000); // Check every 5 minutes
  }
};

export default sessionService; 