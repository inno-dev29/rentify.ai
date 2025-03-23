'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get('redirect') || '/';
  const { login, isAuthenticated, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState<{
    username?: string;
    password?: string;
    general?: string;
  }>({});
  const [loading, setLoading] = useState(false);

  // Check if already logged in
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push(redirectPath);
    }
  }, [isAuthenticated, isLoading, redirectPath, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user types
    if (errors[name as keyof typeof errors]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  const validateForm = () => {
    const newErrors: {
      username?: string;
      password?: string;
    } = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    console.log('Attempting login with username:', formData.username);
    setLoading(true);
    try {
      console.log('Making login API request...');
      const response = await login({
        username: formData.username,
        password: formData.password
      });
      
      console.log('Login API response:', response);
      
      if (response && response.key) {
        console.log('Login successful');
        router.push(redirectPath);
      } else {
        console.warn('Login response missing auth key:', response);
        setErrors({
          general: 'Invalid login response. Please try again.'
        });
      }
    } catch (error: any) {
      console.error('Login error:', error);
      
      // Check if it's a network error (from our custom handling)
      if (error.isNetworkError || error.message?.includes('Network error')) {
        setErrors({
          general: 'Cannot connect to the authentication server. This might be caused by network issues or browser security features blocking the request. Please check your connection and try again.'
        });
        return;
      }
      
      // Handle the specific TokenSerializer error from Django
      if (error.message?.includes('TokenSerializer') || error.message?.includes('LoginView-ImportError')) {
        setErrors({
          general: 'The authentication system is temporarily unavailable. This is a server-side configuration issue. Please try again later or contact support.'
        });
        return;
      }
      
      // Handle different error cases
      if (error.status === 401) {
        setErrors({
          general: 'Invalid username or password. Please try again.'
        });
      } else if (error.status === 500) {
        setErrors({
          general: 'The server encountered an error. Please try again later or contact support.'
        });
      } else if (error.status === 0 || error.message?.includes('Failed to fetch')) {
        // Network error - likely CORS or server unreachable
        setErrors({
          general: 'Unable to connect to the authentication server. Please try again later or check if you have browser extensions that might be blocking the request.'
        });
      } else if (error.errors) {
        // Handle field-specific errors
        const fieldErrors: any = {};
        
        if (error.errors.username) {
          fieldErrors.username = error.errors.username;
        }
        
        if (error.errors.password) {
          fieldErrors.password = error.errors.password;
        }
        
        if (error.errors.non_field_errors) {
          fieldErrors.general = error.errors.non_field_errors[0] || 'Invalid login credentials';
        }
        
        if (Object.keys(fieldErrors).length > 0) {
          setErrors(fieldErrors);
        } else {
          setErrors({
            general: error.message || 'Failed to login. Please check your credentials.'
          });
        }
      } else {
        setErrors({
          general: error.message || 'Failed to login. Please check your credentials.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // If still checking auth status, show loading spinner
  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="flex justify-center items-center min-h-[70vh]">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Log in</CardTitle>
          <CardDescription>
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            {errors.general && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
                {errors.general}
              </div>
            )}
            
            <div className="mb-4">
              <label htmlFor="username" className="block text-sm font-medium text-secondary mb-1">
                Username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className={`w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.username ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username}</p>
              )}
            </div>
            
            <div className="mb-4">
              <label htmlFor="password" className="block text-sm font-medium text-secondary mb-1">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.password ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>
            
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Log in'}
            </Button>
            
            <p className="mt-4 text-xs text-gray-500 text-center">
              For security reasons, your session will automatically expire after 15 minutes of inactivity.
            </p>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col items-center justify-center">
          <div className="mt-2">
            <Link href="/forgot-password" className="text-sm text-blue-600 hover:underline">
              Forgot password?
            </Link>
          </div>
          <div className="mt-4 text-center">
            <p className="text-secondary">
              Don't have an account?{' '}
              <Link href="/register" className="text-blue-600 hover:underline">
                Sign up
              </Link>
            </p>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
} 