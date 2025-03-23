from rest_framework import serializers
from .models import User, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model"""
    
    class Meta:
        model = UserProfile
        exclude = ('user',)

class UserSerializer(serializers.ModelSerializer):
    """Base serializer for the User model"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                  'phone', 'profile_image', 'bio', 'is_verified', 'profile', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'is_verified')

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 
                  'last_name', 'user_type', 'phone')
    
    def validate(self, data):
        """Ensure passwords match"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords must match.")
        return data
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class UserDetailSerializer(UserSerializer):
    """Detailed user serializer with additional fields"""
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('created_at', 'updated_at')

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'bio', 'profile')
    
    def update(self, instance, validated_data):
        """Update user and nested profile"""
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data:
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
        
        return instance 