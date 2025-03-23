'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService from '../api/services/authService';
import sessionService from '../api/services/sessionService';

// Define the shape of the user object
type User = {
  id?: number;
  username: string;
  email?: string;
  is_staff?: boolean;
  [key: string]: any; // Allow for additional properties
};

// Define the shape of the auth context
type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  login: (credentials: { username: string; password: string }) => Promise<any>;
  logout: () => Promise<void>;
  refreshAuthState: () => void;
};

// Create the context with a default value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize session service
  useEffect(() => {
    sessionService.init();
  }, []);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
    
    // Listen for storage events (for multi-tab synchronization)
    window.addEventListener('storage', onStorageChange);
    
    // Listen for custom session change events
    window.addEventListener('session_change', onSessionChange);
    
    return () => {
      window.removeEventListener('storage', onStorageChange);
      window.removeEventListener('session_change', onSessionChange);
    };
  }, []);

  // Handle storage changes (for multi-tab synchronization)
  const onStorageChange = (event: StorageEvent) => {
    if (event.key === 'auth_token' || event.key === 'user_data' || event.key === 'session_sync') {
      checkAuthStatus();
    }
  };

  // Handle session change events
  const onSessionChange = (event: Event) => {
    const customEvent = event as CustomEvent<{ action: string }>;
    console.log('Session change event:', customEvent.detail);
    checkAuthStatus();
  };

  // Check if user is authenticated and get user data
  const checkAuthStatus = async () => {
    setIsLoading(true);
    console.log('Checking authentication status...');
    
    try {
      // First check if a valid session exists
      const hasSession = sessionService.hasValidSession();
      
      if (!hasSession) {
        // No valid session found
        console.log('No valid session found');
        setUser(null);
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }
      
      // Try to get user data from session
      const userData = sessionService.getUserData();
      if (userData) {
        console.log('User data retrieved from session:', userData);
        setUser(userData);
        setIsAuthenticated(true);
        setIsLoading(false);
        
        // Verify token in background
        sessionService.verifySession()
          .then(isValid => {
            if (!isValid) {
              console.log('Session became invalid during verification');
              setUser(null);
              setIsAuthenticated(false);
            }
          })
          .catch(error => {
            console.error('Error during session verification:', error);
          });
        
        return;
      }
      
      // If we don't have user data but have a token, verify and fetch user data
      const isValid = await sessionService.verifySession();
      console.log('Session verification result:', isValid);
      
      if (isValid) {
        try {
          const userData = await authService.getCurrentUser();
          console.log('User data retrieved from API:', userData);
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Error fetching user data:', error);
          setUser(null);
          setIsAuthenticated(false);
          // Session is invalid, clear it
          sessionService.clearSession();
        }
      } else {
        // Session is invalid
        console.log('Session is invalid or expired');
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error during authentication check:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Login function
  const login = async (credentials: { username: string; password: string }) => {
    try {
      const response = await authService.login(credentials);
      await checkAuthStatus(); // Refresh auth state after login
      return response;
    } catch (error) {
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  // Function to manually refresh auth state
  const refreshAuthState = () => {
    checkAuthStatus();
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    isAdmin: user?.is_staff === true,
    login,
    logout,
    refreshAuthState
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use the auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 