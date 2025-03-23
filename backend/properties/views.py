from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Property, PropertyImage, Amenity
from .serializers import (
    PropertySerializer, PropertyDetailSerializer, PropertyListSerializer,
    PropertyImageSerializer, AmenitySerializer
)
from django.db import models

class PropertyListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating properties
    """
    queryset = Property.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PropertyDetailSerializer
        return PropertyListSerializer
    
    def get_permissions(self):
        """Allow anyone to list properties, but only leasers can create them"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        """Set the leaser to the authenticated user"""
        serializer.save(leaser=self.request.user)
        
    def get_queryset(self):
        """
        Filter properties based on query parameters
        """
        queryset = Property.objects.all()
        
        # By default, only show active properties
        status = self.request.query_params.get('status', 'active')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by property type
        property_type = self.request.query_params.get('type', None)
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        # Filter by location (city or country)
        location = self.request.query_params.get('location', None)
        if location:
            location_terms = location.split(',')
            for term in location_terms:
                term = term.strip()
                if term:
                    # Use a logical OR for city and country
                    queryset = queryset.filter(
                        models.Q(city__icontains=term) | 
                        models.Q(country__icontains=term) |
                        models.Q(state__icontains=term)
                    )
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            try:
                min_price = float(min_price)
                queryset = queryset.filter(base_price__gte=min_price)
            except (ValueError, TypeError):
                pass
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            try:
                max_price = float(max_price)
                queryset = queryset.filter(base_price__lte=max_price)
            except (ValueError, TypeError):
                pass
                
        # Filter by bedroom count
        min_bedrooms = self.request.query_params.get('min_bedrooms', None)
        if min_bedrooms:
            try:
                min_bedrooms = int(min_bedrooms)
                queryset = queryset.filter(bedroom_count__gte=min_bedrooms)
            except (ValueError, TypeError):
                pass
                
        # Filter by bathroom count
        min_bathrooms = self.request.query_params.get('min_bathrooms', None)
        if min_bathrooms:
            try:
                min_bathrooms = float(min_bathrooms)
                queryset = queryset.filter(bathroom_count__gte=min_bathrooms)
            except (ValueError, TypeError):
                pass
                
        # Filter by max guests
        min_guests = self.request.query_params.get('min_guests', None)
        if min_guests:
            try:
                min_guests = int(min_guests)
                queryset = queryset.filter(max_guests__gte=min_guests)
            except (ValueError, TypeError):
                pass
        
        # Filter by amenities
        amenities = self.request.query_params.get('amenities', None)
        if amenities:
            amenity_ids = [id.strip() for id in amenities.split(',') if id.strip()]
            for amenity_id in amenity_ids:
                try:
                    amenity_id = int(amenity_id)
                    queryset = queryset.filter(amenities__id=amenity_id)
                except (ValueError, TypeError):
                    # If ID is not an integer, try to filter by name
                    queryset = queryset.filter(amenities__name__icontains=amenity_id)
        
        return queryset

class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific property
    """
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializer
    
    def get_permissions(self):
        """Allow anyone to view properties, but only the leaser can update/delete them"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def check_object_permissions(self, request, obj):
        """Ensure only the leaser can update/delete the property"""
        if request.method in ['PUT', 'PATCH', 'DELETE'] and obj.leaser != request.user:
            self.permission_denied(request)
        return super().check_object_permissions(request, obj)

class PropertyImageListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating property images
    """
    serializer_class = PropertyImageSerializer
    
    def get_queryset(self):
        property_id = self.kwargs.get('property_id')
        return PropertyImage.objects.filter(property_id=property_id)
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        property_id = self.kwargs.get('property_id')
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Check if the user is the leaser
        if property_obj.leaser != self.request.user:
            self.permission_denied(self.request)
        
        serializer.save(property=property_obj)

class PropertyImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific property image
    """
    serializer_class = PropertyImageSerializer
    
    def get_queryset(self):
        property_id = self.kwargs.get('property_id')
        return PropertyImage.objects.filter(property_id=property_id)
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def check_object_permissions(self, request, obj):
        """Ensure only the leaser can update/delete the image"""
        if obj.property.leaser != request.user:
            self.permission_denied(request)
        return super().check_object_permissions(request, obj)

class AmenityListView(generics.ListAPIView):
    """
    API endpoint for listing amenities
    """
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]
