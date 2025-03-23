from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Booking
from properties.models import Property
from .serializers import (
    BookingSerializer, BookingDetailSerializer, BookingCreateSerializer,
    BookingStatusUpdateSerializer
)
from rest_framework.exceptions import ValidationError
import logging

class BookingListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating bookings
    """
    def get_queryset(self):
        """
        Return bookings that the current user has either made or received (as a property leaser)
        """
        logger = logging.getLogger('django')
        
        try:
            user = self.request.user
            return Booking.objects.filter(
                Q(renter=user) | Q(property__leaser=user)
            ).select_related('property', 'renter')
        except Exception as e:
            # Log the error but return an empty queryset rather than 500 error
            logger.error(f"Error retrieving bookings in get_queryset: {str(e)}")
            return Booking.objects.none()
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to handle errors gracefully
        """
        logger = logging.getLogger('django')
        
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            # Log the error but return an empty list response
            logger.error(f"Error in booking list view: {str(e)}")
            
            # Return a proper paginated empty response
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
            })
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookingCreateSerializer
        return BookingDetailSerializer
    
    def get_permissions(self):
        """
        Allow authenticated users to list and create bookings
        """
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """
        Set the renter to the current user
        """
        property_id = serializer.validated_data.get('property').id
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Ensure the user is not booking their own property
        if property_obj.leaser == self.request.user:
            # Using raise_exception=True causes the validation error to be properly handled
            raise ValidationError({"detail": "You cannot book your own property."})
        
        # If we get here, save the booking with the current user as renter
        booking = serializer.save(renter=self.request.user)
        
        # Log successful booking creation for debugging
        print(f"Booking created: ID {booking.id} - {booking.property.title} - {booking.start_date} to {booking.end_date}")
        
        return booking

class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific booking
    """
    serializer_class = BookingDetailSerializer
    
    def get_queryset(self):
        """
        Return bookings that the current user has either made or received (as a property leaser)
        """
        user = self.request.user
        return Booking.objects.filter(
            Q(renter=user) | Q(property__leaser=user)
        ).select_related('property', 'renter')
    
    def get_permissions(self):
        """
        Allow authenticated users to view, update, and delete bookings
        """
        return [permissions.IsAuthenticated()]
    
    def check_object_permissions(self, request, obj):
        """
        Ensure only the renter can update/delete the booking
        """
        if request.method in ['PUT', 'PATCH', 'DELETE'] and obj.renter != request.user:
            self.permission_denied(request)
        return super().check_object_permissions(request, obj)

class BookingStatusUpdateView(generics.UpdateAPIView):
    """
    API endpoint for updating the status of a booking (e.g., accept, reject)
    """
    serializer_class = BookingStatusUpdateSerializer
    
    def get_queryset(self):
        """
        Return bookings that the current user has either made (as renter) or received (as a property leaser)
        This ensures both renters and property owners can update status
        """
        user = self.request.user
        return Booking.objects.filter(
            Q(renter=user) | Q(property__leaser=user)
        ).select_related('property', 'renter')
    
    def get_permissions(self):
        """
        Allow authenticated users to update booking status
        """
        return [permissions.IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        """
        Update the booking status
        """
        logger = logging.getLogger('django')
        
        try:
            # Get the booking object
            try:
                instance = self.get_object()
            except Exception as e:
                logger.error(f"[BOOKING] Handled exception in BookingStatusUpdateView: {type(e).__name__}: {str(e)}")
                logger.info(f"Response status: {getattr(e, 'status_code', 'Unknown')}")
                logger.info(f"Response data: {getattr(e, 'detail', 'No detail available')}")
                return Response(
                    {"detail": str(e)},
                    status=getattr(e, 'status_code', status.HTTP_404_NOT_FOUND)
                )
                
            # Parse and validate the request data
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Check permissions based on the requested status change
            new_status = serializer.validated_data.get('status')
            
            # Renters can only cancel their own bookings
            if new_status == 'cancelled' and instance.renter == request.user:
                # Allow cancellation by the renter
                pass
            # Property leasers can update any status for their property bookings
            elif instance.property.leaser == request.user:
                # Allow any status update by the property leaser
                pass
            else:
                # Deny permission for any other case
                return Response(
                    {"detail": "You do not have permission to update this booking's status."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Perform the update if permissions were granted
            self.perform_update(serializer)
            
            # Clear cache if needed
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            
            return Response(serializer.data)
        
        except Exception as e:
            # Log the error with a special prefix
            logger.error(f"[BOOKING] Unhandled exception in BookingStatusUpdateView: {type(e).__name__}: {str(e)}")
            # Return a helpful error response
            return Response(
                {"detail": f"An error occurred while updating booking status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PropertyAvailabilityView(APIView):
    """
    API endpoint for checking property availability for specific dates
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, property_id):
        """
        Check property availability and return a list of unavailable dates
        
        Query Parameters:
        - start_date: The start date (YYYY-MM-DD) for availability checking
        - end_date: The end date (YYYY-MM-DD) for availability checking
        
        Returns:
        - A list of unavailable dates within the specified range
        - Availability status for the entire period
        """
        # Get logger for structured logging
        logger = logging.getLogger('django')
        logger.info(f"Checking availability for property {property_id}")
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"detail": "Both start_date and end_date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if start_date > end_date:
            return Response(
                {"detail": "End date must be after start date."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the property exists
        try:
            property_obj = get_object_or_404(Property, id=property_id)
        except Exception as e:
            logger.error(f"Error retrieving property {property_id}: {str(e)}")
            return Response(
                {"detail": "Property not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all overlapping bookings (that are pending or confirmed)
        overlapping_bookings = Booking.objects.filter(
            property=property_obj,
            status__in=['pending', 'confirmed'],
        ).filter(
            # Get bookings that overlap with the requested date range
            Q(start_date__lte=end_date, end_date__gte=start_date)
        ).order_by('start_date')
        
        # For each overlapping booking, generate the unavailable dates
        unavailable_dates = set()
        
        for booking in overlapping_bookings:
            # Limit to the requested date range
            booking_start = max(booking.start_date, start_date)
            booking_end = min(booking.end_date, end_date)
            
            # Add all dates in the booking range to the unavailable dates set
            current_date = booking_start
            while current_date <= booking_end:
                unavailable_dates.add(current_date.isoformat())
                # Use timedelta to properly increment the date by one day
                current_date = (current_date + timedelta(days=1))
        
        # Convert set to sorted list for consistent output
        unavailable_dates_list = sorted(list(unavailable_dates))
        
        # Check if the entire requested period is available
        specific_period_available = len(unavailable_dates) == 0
        
        logger.info(f"Found {len(unavailable_dates)} unavailable dates for property {property_id}")
        
        return Response({
            "property_id": property_id,
            "unavailable_dates": unavailable_dates_list,
            "available": specific_period_available,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }, status=status.HTTP_200_OK)

class PropertyBookingsView(APIView):
    """
    API endpoint for retrieving all bookings for a specific property
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, property_id):
        """
        Get all bookings for a property
        
        Returns:
        - A list of all bookings for the property
        """
        # Get logger for structured logging
        logger = logging.getLogger('django')
        logger.info(f"Retrieving bookings for property {property_id}")
        
        # Check if the property exists
        try:
            property_obj = get_object_or_404(Property, id=property_id)
        except Exception as e:
            logger.error(f"Error retrieving property {property_id}: {str(e)}")
            return Response(
                {"detail": "Property not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all bookings for the property (pending or confirmed)
        bookings = Booking.objects.filter(
            property=property_obj,
            status__in=['pending', 'confirmed']
        ).order_by('start_date')
        
        # Serialize the bookings
        try:
            serializer = BookingSerializer(bookings, many=True)
            logger.info(f"Found {len(bookings)} bookings for property {property_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            # Log error with a special prefix for easier filtering
            logger.error(f"[BOOKING ERROR] Unhandled exception in PropertyBookingsView handling GET to /api/properties/{property_id}/bookings/")
            logger.error(f"User: {request.user.username}")
            logger.error(f"Data: {request.data}")
            logger.error(f"Error: {type(e).__name__}: {str(e)}")
            
            # Add traceback for more detailed debugging
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            # Return a warning but don't crash
            logger.warning(f"Returning empty list for failed booking listing request to /api/properties/{property_id}/bookings/")
            return Response([], status=status.HTTP_200_OK)
