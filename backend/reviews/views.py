from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from .models import Review, ReviewImage
from bookings.models import Booking
from properties.models import Property
from .serializers import (
    ReviewSerializer, ReviewDetailSerializer, ReviewCreateSerializer,
    ReviewResponseSerializer, ReviewImageSerializer
)

class ReviewListView(generics.ListAPIView):
    """
    API endpoint for listing all reviews
    """
    serializer_class = ReviewDetailSerializer
    
    def get_queryset(self):
        """
        Return reviews related to the current user (as reviewer or property leaser)
        """
        user = self.request.user
        if user.is_authenticated:
            return Review.objects.filter(
                reviewer=user
            ).select_related('property', 'reviewer', 'booking')
        return Review.objects.none()
    
    def get_permissions(self):
        """
        Allow authenticated users to list reviews
        """
        return [permissions.IsAuthenticated()]

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific review
    """
    serializer_class = ReviewDetailSerializer
    
    def get_queryset(self):
        """
        Return reviews that the current user has created
        """
        user = self.request.user
        return Review.objects.filter(reviewer=user).select_related('property', 'reviewer', 'booking')
    
    def get_permissions(self):
        """
        Allow authenticated users to interact with reviews
        """
        return [permissions.IsAuthenticated()]
    
    def check_object_permissions(self, request, obj):
        """
        Ensure only the reviewer can update/delete the review
        """
        if obj.reviewer != request.user:
            self.permission_denied(request)
        return super().check_object_permissions(request, obj)

class PropertyReviewListView(generics.ListAPIView):
    """
    API endpoint for listing all reviews for a specific property
    """
    serializer_class = ReviewDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Return reviews for a specific property
        """
        property_id = self.kwargs.get('property_id')
        return Review.objects.filter(
            property_id=property_id
        ).select_related('reviewer', 'booking')
    
    def list(self, request, *args, **kwargs):
        """
        List reviews for a property with average ratings
        """
        property_id = self.kwargs.get('property_id')
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Get the average ratings
        avg_ratings = Review.objects.filter(property=property_obj).aggregate(
            avg_cleanliness=Avg('cleanliness_rating'),
            avg_communication=Avg('communication_rating'),
            avg_accuracy=Avg('accuracy_rating'),
            avg_location=Avg('location_rating'),
            avg_value=Avg('value_rating'),
            avg_overall=Avg('overall_rating')
        )
        
        # Get the reviews
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'average_ratings': avg_ratings,
            'reviews': serializer.data
        })

class BookingReviewCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a review for a specific booking
    """
    serializer_class = ReviewCreateSerializer
    
    def get_permissions(self):
        """
        Allow authenticated users to create reviews
        """
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """
        Create a review for a booking
        """
        booking_id = serializer.validated_data.pop('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Ensure the user is the renter of the booking
        if booking.renter != self.request.user:
            self.permission_denied(self.request)
        
        # Ensure the booking is completed
        if booking.status != 'completed':
            return Response(
                {"detail": "Cannot review a booking that is not completed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure the booking has not been reviewed yet
        if Review.objects.filter(booking=booking).exists():
            return Response(
                {"detail": "This booking has already been reviewed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(
            reviewer=self.request.user,
            booking=booking,
            property=booking.property
        )

class ReviewImageListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating review images
    """
    serializer_class = ReviewImageSerializer
    
    def get_queryset(self):
        """
        Return images for a specific review
        """
        review_id = self.kwargs.get('review_id')
        return ReviewImage.objects.filter(review_id=review_id)
    
    def get_permissions(self):
        """
        Allow anyone to view review images, but only the reviewer can add images
        """
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        """
        Create a review image
        """
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id)
        
        # Ensure the user is the reviewer
        if review.reviewer != self.request.user:
            self.permission_denied(self.request)
        
        serializer.save(review=review)

class ReviewImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific review image
    """
    serializer_class = ReviewImageSerializer
    
    def get_queryset(self):
        """
        Return images for a specific review
        """
        review_id = self.kwargs.get('review_id')
        return ReviewImage.objects.filter(review_id=review_id)
    
    def get_permissions(self):
        """
        Allow anyone to view review images, but only the reviewer can update/delete images
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def check_object_permissions(self, request, obj):
        """
        Ensure only the reviewer can update/delete the review image
        """
        if request.method in ['PUT', 'PATCH', 'DELETE'] and obj.review.reviewer != request.user:
            self.permission_denied(request)
        return super().check_object_permissions(request, obj)
