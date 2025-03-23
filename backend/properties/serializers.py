from rest_framework import serializers
from .models import Property, PropertyImage, Amenity
from users.serializers import UserSerializer

class AmenitySerializer(serializers.ModelSerializer):
    """
    Serializer for Amenity model
    """
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon']

class PropertyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyImage model
    """
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'caption', 'is_primary', 'upload_date']
        read_only_fields = ['upload_date']

class PropertySerializer(serializers.ModelSerializer):
    """
    Serializer for Property model with basic information
    """
    primary_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'property_type', 'status',
            'address_line1', 'address_line2', 'city', 'state', 
            'postal_code', 'country', 'latitude', 'longitude',
            'bedroom_count', 'bathroom_count', 'max_guests', 'square_feet',
            'base_price', 'cleaning_fee', 'service_fee', 'extra_guest_fee', 'min_nights',
            'primary_image_url', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_primary_image_url(self, obj):
        """
        Get the URL of the primary image of the property
        """
        request = self.context.get('request')
        primary_image = obj.primary_image
        
        if primary_image and primary_image.image:
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None

class PropertyDetailSerializer(PropertySerializer):
    """
    Detailed serializer for Property model with additional information
    """
    images = PropertyImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    leaser = UserSerializer(read_only=True)
    amenity_ids = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='amenities'
    )
    
    class Meta(PropertySerializer.Meta):
        fields = PropertySerializer.Meta.fields + [
            'images', 'amenities', 'leaser', 'amenity_ids',
            'house_rules', 'cancellation_policy', 'check_in_time', 'check_out_time',
            'llm_summary'
        ]
        read_only_fields = PropertySerializer.Meta.read_only_fields + ['llm_summary']
    
    def create(self, validated_data):
        """
        Create a new Property with amenities
        """
        # Extract amenities from validated data
        amenities = validated_data.pop('amenities', [])
        
        # Create property instance
        property_instance = Property.objects.create(**validated_data)
        
        # Add amenities
        if amenities:
            property_instance.amenities.set(amenities)
        
        return property_instance
    
    def update(self, instance, validated_data):
        """
        Update a Property with amenities
        """
        # Extract amenities from validated_data
        amenities = validated_data.pop('amenities', None)
        
        # Update property instance fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        # Update amenities if provided
        if amenities is not None:
            instance.amenities.set(amenities)
        
        return instance

class PropertyListSerializer(PropertySerializer):
    """
    Serializer for listing properties with essential information
    """
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'city', 'country',
            'bedroom_count', 'bathroom_count', 'max_guests', 
            'base_price', 'primary_image_url'
        ] 