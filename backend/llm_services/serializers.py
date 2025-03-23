from rest_framework import serializers
from .models import PropertySummary, Persona, Recommendation, RecommendationItem
from properties.serializers import PropertyListSerializer
from users.serializers import UserSerializer

class PropertySummarySerializer(serializers.ModelSerializer):
    """
    Serializer for PropertySummary model
    """
    class Meta:
        model = PropertySummary
        fields = [
            'id', 'property', 'summary_text', 'highlights',
            'generate_version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class PropertySummaryDetailSerializer(PropertySummarySerializer):
    """
    Detailed serializer for PropertySummary with property details
    """
    property = PropertyListSerializer(read_only=True)
    
    class Meta(PropertySummarySerializer.Meta):
        pass

class PersonaSerializer(serializers.ModelSerializer):
    """
    Serializer for Persona model
    """
    class Meta:
        model = Persona
        fields = [
            'id', 'user', 'property', 'persona_type', 'persona_data',
            'generate_version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class PersonaDetailSerializer(PersonaSerializer):
    """
    Detailed serializer for Persona with user or property details
    """
    user = UserSerializer(read_only=True)
    property = PropertyListSerializer(read_only=True)
    
    class Meta(PersonaSerializer.Meta):
        pass

class RecommendationItemSerializer(serializers.ModelSerializer):
    """
    Serializer for RecommendationItem model
    """
    property = PropertyListSerializer(read_only=True)
    
    class Meta:
        model = RecommendationItem
        fields = [
            'id', 'property', 'score', 'reasoning', 'rank'
        ]

class RecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for Recommendation model
    """
    items = RecommendationItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'user', 'items', 'generate_version',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# Additional serializers for API responses

class PropertySummaryResponseSerializer(serializers.Serializer):
    """
    Serializer for property summary response
    """
    summary = serializers.CharField()
    highlights = serializers.ListField(child=serializers.CharField(), required=False)
    generated_at = serializers.DateTimeField()
    property_id = serializers.IntegerField(required=False)
    model = serializers.CharField(required=False)
    created_by = serializers.CharField(required=False)

class PersonaResponseSerializer(serializers.Serializer):
    """
    Serializer for persona response
    """
    persona = serializers.JSONField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

class RecommendationResponseSerializer(serializers.Serializer):
    """
    Serializer for recommendation response
    """
    recommendations = serializers.ListField(child=serializers.JSONField())
    generated_at = serializers.DateTimeField() 