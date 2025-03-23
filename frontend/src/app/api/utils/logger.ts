/**
 * Simple logger utility for consistent logging across the application
 */

// Logger interface
export interface Logger {
  info: (message: string, ...args: any[]) => void;
  debug: (message: string, ...args: any[]) => void;
  warn: (message: string, ...args: any[]) => void;
  error: (message: string, ...args: any[]) => void;
}

/**
 * Create a logger instance with the given context
 * @param context - The context for the logger (usually the component or service name)
 * @returns A logger instance
 */
export const getLogger = (context: string): Logger => {
  return {
    info: (message: string, ...args: any[]) => {
      console.info(`[${context}] ${message}`, ...args);
    },
    debug: (message: string, ...args: any[]) => {
      // Only log debug messages in development
      if (process.env.NODE_ENV !== 'production') {
        console.debug(`[${context}] ${message}`, ...args);
      }
    },
    warn: (message: string, ...args: any[]) => {
      console.warn(`[${context}] ${message}`, ...args);
    },
    error: (message: string, ...args: any[]) => {
      console.error(`[${context}] ${message}`, ...args);
    }
  };
};

/**
 * Get authentication token from localStorage
 * @returns The token or null if not found
 */
export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  // Check for token using correct key name 'auth_token'
  const authToken = localStorage.getItem('auth_token');
  if (authToken) return authToken;
  
  // Fallback to check for 'token' as well (for backward compatibility)
  const legacyToken = localStorage.getItem('token');
  if (legacyToken) {
    // If found in legacy format, migrate it to the current format
    localStorage.setItem('auth_token', legacyToken);
    return legacyToken;
  }
  
  return null;
};

/**
 * Check if user is authenticated by verifying token existence
 * @returns True if authenticated, false otherwise
 */
export const isAuthenticated = (): boolean => {
  return !!getToken();
}; 