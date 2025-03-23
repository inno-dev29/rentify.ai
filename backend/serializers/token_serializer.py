from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model to handle authentication tokens.
    """
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Token
        fields = ('key', 'user')
        
    def get_user(self, obj):
        """
        Get user details to include in the token response.
        """
        user_data = {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'is_staff': obj.user.is_staff,
        }
        
        # Try to get additional user info if available
        try:
            user_data.update({
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'user_type': getattr(obj.user, 'user_type', None),
            })
        except Exception:
            pass
            
        return user_data 