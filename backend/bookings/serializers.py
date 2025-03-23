from rest_framework import serializers
from .models import Booking
from properties.serializers import PropertyListSerializer
from users.serializers import UserSerializer
import logging

class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model
    """
    duration_nights = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property', 'renter', 'start_date', 'end_date',
            'guests_count', 'status', 'total_price', 'base_price_total',
            'cleaning_fee', 'service_fee', 'extra_guest_fee', 
            'is_paid', 'payment_method', 'payment_id',
            'special_requests', 'cancellation_reason',
            'duration_nights', 'is_active', 'is_upcoming', 'is_past',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'leaser_notes']

class BookingDetailSerializer(BookingSerializer):
    """
    Detailed serializer for Booking model with property and renter details
    """
    property = PropertyListSerializer(read_only=True)
    renter = UserSerializer(read_only=True)
    
    class Meta(BookingSerializer.Meta):
        pass

class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new booking
    """
    class Meta:
        model = Booking
        fields = [
            'property', 'start_date', 'end_date', 'guests_count',
            'special_requests'
        ]
    
    def validate(self, data):
        """
        Validate booking dates and availability
        """
        logger = logging.getLogger('django')
        
        try:
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            property_obj = data.get('property')
            
            # Additional validations for required fields
            if not start_date:
                raise serializers.ValidationError({"start_date": "Start date is required"})
            if not end_date:
                raise serializers.ValidationError({"end_date": "End date is required"})
            if not property_obj:
                raise serializers.ValidationError({"property": "Property is required"})
            
            # Check that end date is after start date
            if end_date <= start_date:
                raise serializers.ValidationError({"end_date": "End date must be after start date"})
            
            # Make sure start date is not in the past
            import datetime
            today = datetime.date.today()
            logger.info(f"Validating booking dates - Start date: {start_date}, Today's date: {today}")

            # Allow booking for today's date (equal to today) or future dates (greater than today)
            if start_date < today:
                logger.warning(f"Booking rejected - start date {start_date} is before today {today}")
                raise serializers.ValidationError({"start_date": "Start date cannot be in the past"})
            
            # Check if the property is available for these dates
            overlapping_bookings = Booking.objects.filter(
                property=property_obj,
                start_date__lt=end_date,
                end_date__gt=start_date,
                status__in=['pending', 'confirmed']
            )
            
            # Exclude current booking if updating
            instance = getattr(self, 'instance', None)
            if instance:
                overlapping_bookings = overlapping_bookings.exclude(pk=instance.pk)
            
            if overlapping_bookings.exists():
                raise serializers.ValidationError({
                    "non_field_errors": "Property is not available for these dates", 
                    "booking_conflicts": [b.id for b in overlapping_bookings]
                })
            
            return data
        except serializers.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in booking validation: {str(e)}")
            raise serializers.ValidationError({"non_field_errors": f"Validation error: {str(e)}"})
    
    def create(self, validated_data):
        """
        Create a new booking with calculated prices
        """
        logger = logging.getLogger('django')
        
        try:
            property_obj = validated_data.get('property')
            start_date = validated_data.get('start_date')
            end_date = validated_data.get('end_date')
            guests_count = validated_data.get('guests_count', 1)
            
            # Log booking attempt for debugging
            logger.info(f"Creating booking for property {property_obj.id} ({property_obj.title}) - " +
                       f"Dates: {start_date} to {end_date}, Guests: {guests_count}")
            
            # Additional check to ensure property exists and has necessary fields
            if not hasattr(property_obj, 'base_price') or property_obj.base_price is None:
                logger.error(f"Property {property_obj.id} is missing base_price")
                raise serializers.ValidationError({
                    "property": f"Property {property_obj.id} has invalid pricing information"
                })
                
            # Calculate number of nights
            nights = (end_date - start_date).days
            if nights <= 0:
                logger.error(f"Invalid stay duration: {nights} nights")
                raise serializers.ValidationError({
                    "non_field_errors": "Stay duration must be at least 1 night"
                })
            
            # Calculate prices with safe defaults for null values
            base_price_total = property_obj.base_price * nights
            cleaning_fee = property_obj.cleaning_fee or 0
            service_fee = property_obj.service_fee or 0
            
            # Calculate extra guest fee if applicable
            extra_guest_fee = 0
            if hasattr(property_obj, 'max_guests') and property_obj.max_guests is not None:
                if guests_count > property_obj.max_guests and hasattr(property_obj, 'extra_guest_fee'):
                    extra_guest_fee = (property_obj.extra_guest_fee or 0) * (guests_count - property_obj.max_guests) * nights
            
            # Calculate total price
            total_price = base_price_total + cleaning_fee + service_fee + extra_guest_fee
            
            # Add pricing to validated data
            validated_data['base_price_total'] = base_price_total
            validated_data['cleaning_fee'] = cleaning_fee
            validated_data['service_fee'] = service_fee
            validated_data['extra_guest_fee'] = extra_guest_fee
            validated_data['total_price'] = total_price
            
            # Log the pricing information
            logger.info(f"Booking pricing calculated: Base: {base_price_total}, " +
                       f"Cleaning: {cleaning_fee}, Service: {service_fee}, " +
                       f"Extra Guest: {extra_guest_fee}, Total: {total_price}")
            
            # Create and save the booking
            booking = super().create(validated_data)
            
            # Log success after saving
            logger.info(f"Booking created successfully: ID {booking.id} for property {property_obj.id} ({property_obj.title})")
            
            return booking
            
        except serializers.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Catch all exceptions during booking creation to properly log them
            logger.error(f"Error creating booking: {str(e)}")
            # Convert to ValidationError for better client handling
            raise serializers.ValidationError({"non_field_errors": f"Failed to create booking: {str(e)}"})

class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating booking status
    """
    class Meta:
        model = Booking
        fields = ['status', 'cancellation_reason']
    
    def validate_status(self, value):
        """
        Validate status transition
        """
        booking = self.instance
        valid_transitions = {
            'pending': ['confirmed', 'rejected', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'rejected': [],  # Cannot transition from rejected
            'cancelled': [],  # Cannot transition from cancelled
            'completed': []   # Cannot transition from completed
        }
        
        if value not in valid_transitions.get(booking.status, []):
            raise serializers.ValidationError(f"Cannot transition from '{booking.status}' to '{value}'")
        
        return value 