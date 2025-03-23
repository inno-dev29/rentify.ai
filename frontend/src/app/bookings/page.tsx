'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { format } from 'date-fns';
import authService from '@/app/api/services/authService';
import { bookingService } from '@/app/api/services/bookingService';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle, 
  CardFooter 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Define type for bookings
interface Booking {
  id: number;
  property: {
    id: number;
    title: string;
    city: string;
    country: string;
    primary_image_url?: string;
    property_type?: string;
    bedroom_count?: number;
    bathroom_count?: number;
    base_price?: number;
  };
  renter?: {
    id: number;
    username: string;
    email?: string;
  };
  start_date: string;
  end_date: string;
  status: string;
  total_price: string | number;
  base_price_total?: string | number;
  cleaning_fee?: string | number;
  service_fee?: string | number;
  extra_guest_fee?: string | number;
  duration_nights: number;
  guests_count: number;
  special_requests?: string;
  cancellation_reason?: string;
  is_paid?: boolean;
  created_at?: string;
  updated_at?: string;
}

export default function BookingsPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBookings = async () => {
      if (!authService.isAuthenticated()) {
        router.push('/login?redirect=/bookings');
        return;
      }
      
      try {
        setIsLoading(true);
        const result = await bookingService.getBookings();
        console.log('Bookings result structure:', {
          isArray: Array.isArray(result),
          type: typeof result,
          keys: result ? Object.keys(result) : 'no keys',
          rawResult: result
        });
        
        let bookingsArray: Booking[] = [];
        if (Array.isArray(result)) {
          bookingsArray = result;
        } else {
          // If the result is not an array, check if it's a paginated response
          // This is a fallback in case our bookingService fix didn't work
          bookingsArray = result?.results || [];
          console.log('Extracted bookings array:', bookingsArray);
        }
        
        // Sort bookings - non-cancelled bookings first
        const sortedBookings = [...bookingsArray].sort((a, b) => {
          // First, separate cancelled from non-cancelled
          if (a.status === 'cancelled' && b.status !== 'cancelled') return 1;
          if (a.status !== 'cancelled' && b.status === 'cancelled') return -1;
          
          // For same cancellation status, sort by date (most recent first)
          return new Date(b.start_date).getTime() - new Date(a.start_date).getTime();
        });
        
        console.log('Sorted bookings - non-cancelled first:', sortedBookings);
        setBookings(sortedBookings);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching bookings:', err);
        setError(err.message || 'Failed to load bookings. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchBookings();
  }, [router]);

  const handleCancelBooking = async (bookingId: number) => {
    try {
      if (confirm('Are you sure you want to cancel this booking?')) {
        await bookingService.cancelBooking(bookingId);
        console.log(`Booking ${bookingId} cancelled successfully`);
        
        // Refresh the bookings
        const result = await bookingService.getBookings();
        let bookingsArray: Booking[] = [];
        if (Array.isArray(result)) {
          bookingsArray = result;
        } else {
          bookingsArray = result?.results || [];
        }
        
        // Sort bookings - non-cancelled bookings first
        const sortedBookings = [...bookingsArray].sort((a, b) => {
          // First, separate cancelled from non-cancelled
          if (a.status === 'cancelled' && b.status !== 'cancelled') return 1;
          if (a.status !== 'cancelled' && b.status === 'cancelled') return -1;
          
          // For same cancellation status, sort by date (most recent first)
          return new Date(b.start_date).getTime() - new Date(a.start_date).getTime();
        });
        
        setBookings(sortedBookings);
      }
    } catch (err: any) {
      console.error('Error cancelling booking:', err);
      setError(err.message || 'Failed to cancel booking. Please try again.');
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'rejected':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatPrice = (price: string | number | undefined): string => {
    if (price === undefined) return '$0.00';
    
    if (typeof price === 'string') {
      // If it's already a string, ensure it has the $ symbol
      return price.startsWith('$') ? price : `$${price}`;
    }
    
    // If it's a number, format it with 2 decimal places
    return `$${price.toFixed(2)}`;
  };

  // Function to organize bookings into sections
  const organizeBookingsBySection = (bookings: Booking[]) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Set to start of day for fair comparison
    
    const active = bookings.filter(booking => 
      booking.status !== 'cancelled' && 
      new Date(booking.end_date) >= today
    );
    
    const past = bookings.filter(booking => 
      booking.status !== 'cancelled' && 
      new Date(booking.end_date) < today
    );
    
    const cancelled = bookings.filter(booking => 
      booking.status === 'cancelled'
    );
    
    return { active, past, cancelled };
  };

  // Get organized bookings
  const organizedBookings = organizeBookingsBySection(bookings);
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">My Bookings</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}
      
      {bookings.length > 0 ? (
        <div className="space-y-10">
          {/* Active/Upcoming Bookings */}
          {organizedBookings.active.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4">Active & Upcoming</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {organizedBookings.active.map((booking) => (
                  <Card key={booking.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                    <div className="relative h-48">
                      {booking.property.primary_image_url ? (
                        <Image
                          src={booking.property.primary_image_url}
                          alt={booking.property.title}
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                          <span className="text-gray-400">No image available</span>
                        </div>
                      )}
                      <div className={`absolute top-2 right-2 px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeClass(booking.status)}`}>
                        {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                      </div>
                    </div>
                    
                    <CardHeader>
                      <CardTitle>{booking.property.title}</CardTitle>
                      <CardDescription>{booking.property.city}, {booking.property.country}</CardDescription>
                    </CardHeader>
                    
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Dates:</span>
                          <span className="text-sm">
                            {format(new Date(booking.start_date), 'MMM d, yyyy')} - {format(new Date(booking.end_date), 'MMM d, yyyy')}
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Duration:</span>
                          <span className="text-sm">{booking.duration_nights} nights</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Guests:</span>
                          <span className="text-sm">{booking.guests_count}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Total Price:</span>
                          <span className="text-sm font-semibold">{formatPrice(booking.total_price)}</span>
                        </div>
                        
                        {booking.special_requests && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <span className="text-sm font-medium block mb-1">Special Requests:</span>
                            <p className="text-sm text-gray-600">{booking.special_requests}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                    
                    <CardFooter className="flex justify-between">
                      <Button asChild variant="outline">
                        <Link href={`/properties/${booking.property.id}`}>
                          View Property
                        </Link>
                      </Button>
                      
                      {(booking.status === 'pending' || booking.status === 'confirmed') && (
                        <Button 
                          variant="destructive" 
                          onClick={() => handleCancelBooking(booking.id)}
                        >
                          Cancel
                        </Button>
                      )}
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}
          
          {/* Past Bookings */}
          {organizedBookings.past.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4">Past Bookings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {organizedBookings.past.map((booking) => (
                  <Card key={booking.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                    <div className="relative h-48">
                      {booking.property.primary_image_url ? (
                        <Image
                          src={booking.property.primary_image_url}
                          alt={booking.property.title}
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                          <span className="text-gray-400">No image available</span>
                        </div>
                      )}
                      <div className={`absolute top-2 right-2 px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeClass(booking.status)}`}>
                        {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                      </div>
                    </div>
                    
                    <CardHeader>
                      <CardTitle>{booking.property.title}</CardTitle>
                      <CardDescription>{booking.property.city}, {booking.property.country}</CardDescription>
                    </CardHeader>
                    
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Dates:</span>
                          <span className="text-sm">
                            {format(new Date(booking.start_date), 'MMM d, yyyy')} - {format(new Date(booking.end_date), 'MMM d, yyyy')}
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Duration:</span>
                          <span className="text-sm">{booking.duration_nights} nights</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Guests:</span>
                          <span className="text-sm">{booking.guests_count}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Total Price:</span>
                          <span className="text-sm font-semibold">{formatPrice(booking.total_price)}</span>
                        </div>
                        
                        {booking.special_requests && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <span className="text-sm font-medium block mb-1">Special Requests:</span>
                            <p className="text-sm text-gray-600">{booking.special_requests}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                    
                    <CardFooter className="flex justify-between">
                      <Button asChild variant="outline">
                        <Link href={`/properties/${booking.property.id}`}>
                          View Property
                        </Link>
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}
          
          {/* Cancelled Bookings */}
          {organizedBookings.cancelled.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold mb-4">Cancelled</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {organizedBookings.cancelled.map((booking) => (
                  <Card key={booking.id} className="overflow-hidden hover:shadow-lg transition-shadow opacity-70">
                    <div className="relative h-48">
                      {booking.property.primary_image_url ? (
                        <Image
                          src={booking.property.primary_image_url}
                          alt={booking.property.title}
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                          <span className="text-gray-400">No image available</span>
                        </div>
                      )}
                      <div className={`absolute top-2 right-2 px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeClass(booking.status)}`}>
                        {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                      </div>
                    </div>
                    
                    <CardHeader>
                      <CardTitle>{booking.property.title}</CardTitle>
                      <CardDescription>{booking.property.city}, {booking.property.country}</CardDescription>
                    </CardHeader>
                    
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Dates:</span>
                          <span className="text-sm">
                            {format(new Date(booking.start_date), 'MMM d, yyyy')} - {format(new Date(booking.end_date), 'MMM d, yyyy')}
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Duration:</span>
                          <span className="text-sm">{booking.duration_nights} nights</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Guests:</span>
                          <span className="text-sm">{booking.guests_count}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Total Price:</span>
                          <span className="text-sm font-semibold">{formatPrice(booking.total_price)}</span>
                        </div>
                        
                        {booking.cancellation_reason && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <span className="text-sm font-medium block mb-1">Cancellation Reason:</span>
                            <p className="text-sm text-gray-600">{booking.cancellation_reason}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                    
                    <CardFooter className="flex justify-between">
                      <Button asChild variant="outline">
                        <Link href={`/properties/${booking.property.id}`}>
                          View Property
                        </Link>
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg p-8 text-center">
          <h2 className="text-xl font-semibold mb-4">No Bookings Yet</h2>
          <p className="text-gray-600 mb-6">
            You don't have any bookings yet. Start exploring properties and book your next stay!
          </p>
          <Button asChild>
            <Link href="/">Explore Properties</Link>
          </Button>
        </div>
      )}
    </div>
  );
} 