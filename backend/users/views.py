from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import (
    UserSerializer, UserDetailSerializer, UserRegistrationSerializer, UserUpdateSerializer
)
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
import uuid
import datetime

User = get_user_model()

# Create your views here.

class IsUserOrAdmin(permissions.BasePermission):
    """
    Permission to only allow users to access their own resources or admin access
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff

class UserRegistrationView(APIView):
    """
    API endpoint for user registration
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Register a new user
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create auth token for the user
            token, created = Token.objects.get_or_create(user=user)
            response_data = serializer.data
            response_data['token'] = token.key
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API endpoint for user login
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Authenticate and login a user
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"detail": "User account is not active."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "key": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        })

class UserProfileView(APIView):
    """
    API endpoint for retrieving and updating the authenticated user's profile
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Retrieve the authenticated user's profile
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        """
        Update the authenticated user's profile
        """
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a specific user's public profile
    """
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Return all active users
        """
        return User.objects.filter(is_active=True)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a user's public profile
        """
        user = self.get_object()
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

class VerifyEmailView(APIView):
    """
    API endpoint for email verification
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """
        Verify a user's email using the provided token
        """
        try:
            # In a real app, we would validate the token against our database
            # For now, we'll just mark the user as active if they have this token
            user = User.objects.get(username=request.GET.get('user'))
            user.is_active = True
            user.save()
            
            return Response({
                "detail": "Email verified successfully. You can now log in."
            })
        except User.DoesNotExist:
            return Response({
                "detail": "Invalid verification link."
            }, status=status.HTTP_400_BAD_REQUEST)

class TokenVerifyView(APIView):
    """
    API endpoint for token verification
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Verify if a token is valid
        """
        token = request.data.get('token', None)
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Attempt to find the token in the database
            token_obj = Token.objects.get(key=token)
            
            # Check if the user associated with the token is active
            if not token_obj.user.is_active:
                return Response({"detail": "User is inactive."}, status=status.HTTP_401_UNAUTHORIZED)
                
            # Return the user data along with the verification status
            user = token_obj.user
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
            }
                
            return Response({
                "detail": "Token is valid.",
                "user": user_data
            }, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
