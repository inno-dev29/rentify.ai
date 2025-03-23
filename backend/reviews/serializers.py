from rest_framework import serializers
from .models import Review, ReviewImage
from bookings.serializers import BookingSerializer
from properties.serializers import PropertyListSerializer
from users.serializers import UserSerializer

class ReviewImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ReviewImage model
    """
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'caption', 'upload_date']
        read_only_fields = ['upload_date']

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model
    """
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'property', 'booking', 'reviewer',
            'overall_rating', 'cleanliness_rating', 'accuracy_rating',
            'location_rating', 'value_rating', 'communication_rating',
            'comment', 'leaser_response', 'response_date',
            'is_approved', 'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'leaser_response', 'response_date', 'is_approved']
    
    def get_average_rating(self, obj):
        """
        Get the average rating across all rating categories
        """
        return obj.average_rating()

class ReviewDetailSerializer(ReviewSerializer):
    """
    Detailed serializer for Review model with related data
    """
    property = PropertyListSerializer(read_only=True)
    booking = BookingSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    
    class Meta(ReviewSerializer.Meta):
        fields = ReviewSerializer.Meta.fields + ['images']

class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new review
    """
    booking_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Review
        fields = [
            'booking_id', 'overall_rating', 'cleanliness_rating', 
            'accuracy_rating', 'location_rating', 'value_rating', 
            'communication_rating', 'comment'
        ]
    
    def validate_booking_id(self, value):
        """
        Validate that the booking exists and is completed
        """
        from bookings.models import Booking
        
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking does not exist")
        
        if booking.status != 'completed':
            raise serializers.ValidationError("Cannot review a booking that is not completed")
        
        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("This booking has already been reviewed")
        
        return value

class ReviewResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a leaser response to a review
    """
    class Meta:
        model = Review
        fields = ['leaser_response']
    
    def update(self, instance, validated_data):
        """
        Update the review with a leaser response and set response date
        """
        from django.utils import timezone
        
        instance.leaser_response = validated_data.get('leaser_response')
        instance.response_date = timezone.now()
        instance.save()
        
        return instance 