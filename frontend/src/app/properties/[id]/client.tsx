'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Property } from '@/types/property';
import { propertyService } from '@/app/api/services/propertyService';
import authService from '@/app/api/services/authService';
import { bookingService } from '@/app/api/services/bookingService';
import { Button } from '@/components/ui/button';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { PropertySummary, PropertyPersona } from '@/components/LLM';
import { DatePicker } from '@/components/ui/date-picker';

export default function PropertyDetailClient({ 
  propertyId, 
  initialProperty,
  error: initialError
}: { 
  propertyId: string;
  initialProperty: Property | null;
  error?: string | null;
}) {
  const router = useRouter();
  const [property, setProperty] = useState<Property | null>(initialProperty);
  const [loading, setLoading] = useState(!initialProperty);
  const [error, setError] = useState<string | null>(initialError || null);
  
  // Replace string dates with Date objects
  const [checkInDate, setCheckInDate] = useState<Date | undefined>(undefined);
  const [checkOutDate, setCheckOutDate] = useState<Date | undefined>(undefined);
  
  const [totalPrice, setTotalPrice] = useState<number | null>(null);
  const [bookingStatus, setBookingStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [isPropertyOwner, setIsPropertyOwner] = useState<boolean>(false);
  const [unavailableDates, setUnavailableDates] = useState<string[]>([]);
  const [loadingUnavailableDates, setLoadingUnavailableDates] = useState<boolean>(false);
  
  useEffect(() => {
    // If we don't have initial data, fetch it client-side
    if (!initialProperty) {
      fetchPropertyDetails();
    } else {
      checkOwnership(initialProperty);
      fetchUnavailableDates();
    }
  }, [propertyId, initialProperty]);
  
  const fetchPropertyDetails = async () => {
    setLoading(true);
    try {
      const data = await propertyService.getProperty(parseInt(propertyId));
      setProperty(data);
      setError(null);
      checkOwnership(data);
      fetchUnavailableDates();
    } catch (err) {
      console.error('Failed to fetch property details:', err);
      setError('Failed to load property details. Please try again later.');
    } finally {
      setLoading(false);
    }
  };
  
  // Check if the current user is the owner of the property
  const checkOwnership = async (propertyData: Property) => {
    try {
      const isAuthenticated = authService.isAuthenticated();
      
      if (isAuthenticated) {
        const currentUser = await authService.getCurrentUser();
        
        console.log('Checking ownership:', {
          currentUser,
          propertyData,
          leaser: propertyData.leaser // Log the full leaser data
        });
        
        // First try using the leaser_id property (from type definition)
        if (currentUser && propertyData.leaser_id && 
            currentUser.id === propertyData.leaser_id) {
          console.log('User is the owner of this property (via leaser_id)');
          setIsPropertyOwner(true);
          return;
        }
        
        // If leaser_id isn't available, try using the leaser object
        if (currentUser && propertyData.leaser && 
            currentUser.id === propertyData.leaser.id) {
          console.log('User is the owner of this property (via leaser object)');
          setIsPropertyOwner(true);
          return;
        }
        
        console.log('User is not the owner of this property');
        setIsPropertyOwner(false);
      } else {
        setIsPropertyOwner(false);
      }
    } catch (err) {
      console.error('Error checking property ownership:', err);
      setIsPropertyOwner(false);
    }
  };
  
  // Fetch unavailable dates for the property
  const fetchUnavailableDates = async () => {
    if (!propertyId) return;
    
    setLoadingUnavailableDates(true);
    try {
      // Try to get from the availability endpoint
      const today = new Date();
      const nextYear = new Date();
      nextYear.setFullYear(today.getFullYear() + 1);
      
      const formatDate = (date: Date) => {
        return date.toISOString().split('T')[0];
      };
      
      try {
        const availabilityData = await bookingService.checkAvailability(
          parseInt(propertyId),
          formatDate(today),
          formatDate(nextYear)
        );
        
        if (availabilityData && availabilityData.unavailable_dates) {
          console.log(`Setting ${availabilityData.unavailable_dates.length} unavailable dates`, availabilityData.unavailable_dates);
          setUnavailableDates(availabilityData.unavailable_dates);
        }
      } catch (availabilityError) {
        console.warn('Could not fetch from availability endpoint:', availabilityError);
        
        // Since getPropertyBookings is not available, we'll handle this gracefully
        console.log('Unable to fetch property bookings, availability may not be accurate');
      }
    } catch (err) {
      console.error('Error fetching unavailable dates:', err);
    } finally {
      setLoadingUnavailableDates(false);
    }
  };
  
  // Helper function to convert Date to string in YYYY-MM-DD format
  const formatDateToString = (date: Date | undefined): string => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };
  
  // Update date handlers for the new DatePicker component
  const handleCheckInDateChange = (date: Date | undefined) => {
    setCheckInDate(date);
    
    if (date) {
      // Always set checkout date to the day after check-in
      const nextDay = new Date(date);
      nextDay.setDate(nextDay.getDate() + 1);
      setCheckOutDate(nextDay);
    } else {
      // If check-in date is cleared, also clear checkout date
      setCheckOutDate(undefined);
    }
    
    // Reset total price and booking status when dates change
    setTotalPrice(null);
    setBookingStatus('idle');
    setBookingError(null);
  };
  
  const handleCheckOutDateChange = (date: Date | undefined) => {
    setCheckOutDate(date);
    
    // Reset total price and booking status when dates change
    setTotalPrice(null);
    setBookingStatus('idle');
    setBookingError(null);
  };
  
  const calculateTotalPrice = () => {
    if (!property || !checkInDate || !checkOutDate) {
      return;
    }
    
    // Calculate number of nights
    const timeDiff = checkOutDate.getTime() - checkInDate.getTime();
    const nights = Math.ceil(timeDiff / (1000 * 3600 * 24));
    
    if (nights <= 0) {
      setBookingError('Check-out date must be after check-in date');
      return;
    }
    
    // Calculate total price
    const basePrice = parseFloat(property.base_price.toString());
    const total = basePrice * nights;
    setTotalPrice(total);
    setBookingError(null);
  };
  
  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Enhanced authentication check - try multiple methods
    let isLoggedIn = authService.isAuthenticated();
    console.log('Authentication check before booking:', isLoggedIn ? 'Authenticated' : 'Not authenticated');
    
    if (!isLoggedIn && typeof window !== 'undefined') {
      // Check for auth token or cookie directly as fallback
      const hasAuthToken = localStorage.getItem('auth_token') !== null;
      const hasAuthCookie = document.cookie.includes('auth_token=') || document.cookie.includes('sessionid=');
      
      console.log('Secondary auth checks:', { 
        hasAuthToken, 
        hasAuthCookie
      });
      
      isLoggedIn = hasAuthToken || hasAuthCookie;
      
      // If we have cookies but no token, try to refresh the token
      if (hasAuthCookie && !hasAuthToken) {
        try {
          console.log('Auth cookie found but no token, attempting to refresh authentication');
          const refreshed = await authService.verifyToken(true);
          isLoggedIn = refreshed;
          console.log('Token refresh result:', refreshed ? 'Success' : 'Failed');
        } catch (authError) {
          console.error('Error refreshing authentication:', authError);
        }
      }
    }
    
    if (!isLoggedIn) {
      console.warn('User not authenticated after all checks. Redirecting to login page.');
      setBookingError('You must be logged in to create a booking');
      router.push(`/login?redirect=/properties/${propertyId}`);
      return;
    }
    
    // Extra debug logging for ownership check
    console.log('Property ownership check before booking:', {
      isPropertyOwner,
      propertyId: property?.id,
      propertyLeaserId: property?.leaser_id,
      propertyLeaser: property?.leaser
    });
    
    if (isPropertyOwner) {
      setBookingError('You cannot book your own property');
      return;
    }
    
    // Validate dates
    if (!checkInDate || !checkOutDate) {
      setBookingError('Please select both check-in and check-out dates');
      return;
    }
    
    if (checkInDate >= checkOutDate) {
      setBookingError('Check-out date must be after check-in date');
      return;
    }
    
    // Check if dates are in the future
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const checkInDateMidnight = new Date(checkInDate);
    checkInDateMidnight.setHours(0, 0, 0, 0);
    
    // Compare dates using timestamps to avoid timezone issues
    if (checkInDateMidnight.getTime() < today.getTime()) {
      console.log('Date validation failed:', {
        checkInDate: checkInDate.toISOString(),
        today: today.toISOString(),
        checkInTimestamp: checkInDateMidnight.getTime(),
        todayTimestamp: today.getTime()
      });
      setBookingError('Check-in date cannot be in the past');
      return;
    }
    
    setBookingStatus('loading');
    
    // Create booking data object for easier debugging
    const bookingData = {
      propertyId: parseInt(propertyId),
      startDate: formatDateToString(checkInDate),
      endDate: formatDateToString(checkOutDate),
      guestsCount: property?.max_guests || 1, // Default to property's max guests or 1
      specialRequests: '' // Include empty special requests
    };
    
    console.log('Submitting booking with data:', bookingData);
    
    try {
      // Use bookingService instead of propertyService
      const response = await bookingService.createBooking(bookingData);
      console.log('Booking created successfully:', response);
      
      setBookingStatus('success');
      setBookingError(null);
      
      // Redirect to bookings page after successful booking
      setTimeout(() => {
        router.push('/bookings');
      }, 2000);
      
    } catch (err: any) {
      console.error('Booking error:', err);
      setBookingStatus('error');
      
      // Check for ownership error specifically
      if (err.message && err.message.includes('cannot book your own property')) {
        console.warn('Server confirmed user is the property owner');
        setIsPropertyOwner(true); // Update the state to reflect ownership
        setBookingError('You cannot book your own property');
        return;
      }
      
      // Extract error message from API response
      if (err.message) {
        setBookingError(err.message);
      } else if (err.errors && typeof err.errors === 'object') {
        // Join all error messages
        const errorMessages = Object.values(err.errors).flat().join(', ');
        setBookingError(errorMessages || 'Failed to create booking. Please try again.');
      } else {
        setBookingError('Failed to create booking. Please try again.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="max-w-4xl mx-auto my-8 px-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error || 'Property not found'}
        </div>
        <Button
          onClick={() => router.push('/properties')}
          variant="default"
        >
          Back to Properties
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="mb-6">
        <Button
          onClick={() => router.back()}
          variant="ghost"
          className="flex items-center text-blue-600 hover:text-blue-800 p-0"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-bold mb-4">{property.title}</h1>
          
          <div className="mb-6">
            <p className="text-secondary">{property.city}, {property.country}</p>
          </div>
          
          <Card className="mb-8">
            <CardContent className="flex flex-wrap p-4">
              <div className="mr-6 mb-2">
                <span className="font-semibold">Type:</span> <span className="text-black">{property.property_type}</span>
              </div>
              <div className="mr-6 mb-2">
                <span className="font-semibold">Bedrooms:</span> <span className="text-black">{property.bedroom_count}</span>
              </div>
              <div className="mr-6 mb-2">
                <span className="font-semibold">Bathrooms:</span> <span className="text-black">{property.bathroom_count}</span>
              </div>
              <div className="mr-6 mb-2">
                <span className="font-semibold">Max Guests:</span> <span className="text-black">{property.max_guests}</span>
              </div>
              <div>
                <span className="font-semibold">Price:</span> <span className="text-black">${property.base_price}/night</span>
              </div>
            </CardContent>
          </Card>
          
          {/* Property image */}
          <div className="relative h-72 md:h-96 w-full mb-8 rounded-lg overflow-hidden shadow-md">
            {property.primary_image_url ? (
              <Image
                src={property.primary_image_url}
                alt={property.title}
                fill
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                <span className="text-gray-400">No image available</span>
              </div>
            )}
          </div>
          
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">Description</h2>
            <p className="text-secondary">{property.description || 'No description available.'}</p>
          </div>
          
          {/* AI-Generated Property Summary */}
          <PropertySummary propertyId={propertyId} />
          
          {/* AI-Generated Property Persona */}
          <PropertyPersona propertyId={propertyId} />
        </div>
        
        <div>
          {isPropertyOwner ? (
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle>You own this property</CardTitle>
                <CardDescription>You cannot book your own property</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="text-sm text-secondary mb-4">
                    As the owner, you cannot make bookings for your own property. 
                    You can manage this property and its bookings from your dashboard.
                  </p>
                  <Button 
                    onClick={() => router.push('/my-properties')}
                    className="w-full"
                  >
                    Manage Your Properties
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle>Book this property</CardTitle>
                <CardDescription>
                  <span className="text-2xl font-bold text-primary">${property.base_price}</span> 
                  <span className="text-sm font-normal text-secondary"> per night</span>
                </CardDescription>
              </CardHeader>
              
              <CardContent>
                {loadingUnavailableDates ? (
                  <div className="flex justify-center items-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500 mr-2"></div>
                    <span>Loading availability...</span>
                  </div>
                ) : (
                  <form onSubmit={handleBookingSubmit}>
                    <DatePicker
                      date={checkInDate}
                      setDate={handleCheckInDateChange}
                      unavailableDates={unavailableDates}
                      label="Check-in"
                      className="mb-4"
                    />
                    
                    <DatePicker
                      date={checkOutDate}
                      setDate={handleCheckOutDateChange}
                      unavailableDates={unavailableDates}
                      label="Check-out"
                      className="mb-4"
                      disabled={!checkInDate}
                      minDate={checkInDate}
                    />
                    
                    {(checkInDate && checkOutDate && !totalPrice && !bookingError) && (
                      <Button
                        type="button"
                        onClick={calculateTotalPrice}
                        variant="secondary"
                        className="w-full mb-4"
                      >
                        Calculate Total
                      </Button>
                    )}
                    
                    {totalPrice !== null && (
                      <div className="mb-6 p-3 bg-blue-50 border border-blue-100 rounded-md">
                        <div className="flex justify-between items-center">
                          <span className="text-secondary">Total:</span>
                          <span className="text-xl font-bold text-primary">${totalPrice.toFixed(2)}</span>
                        </div>
                      </div>
                    )}
                    
                    {bookingError && (
                      <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md text-sm">
                        {bookingError}
                      </div>
                    )}
                    
                    {bookingStatus === 'success' && (
                      <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-md text-sm">
                        Booking successful! Redirecting to your bookings...
                      </div>
                    )}
                    
                    <Button
                      type="submit"
                      disabled={bookingStatus === 'loading' || bookingStatus === 'success'}
                      className="w-full"
                    >
                      {bookingStatus === 'loading' ? 'Processing...' : 'Book Now'}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
} 