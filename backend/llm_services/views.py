from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import PropertySummary, Persona, Recommendation, RecommendationItem
from properties.models import Property
from .serializers import (
    PropertySummarySerializer, PropertySummaryDetailSerializer,
    PersonaSerializer, PersonaDetailSerializer,
    RecommendationSerializer, RecommendationItemSerializer,
    PropertySummaryResponseSerializer, PersonaResponseSerializer, RecommendationResponseSerializer
)
from .services.llm_client import (
    generate_property_summary, 
    generate_user_persona, 
    generate_property_persona, 
    generate_recommendations
)
from django.conf import settings
import json
from django.utils import timezone
import os
import logging

User = get_user_model()

class PropertySummaryView(APIView):
    """
    API endpoint for retrieving or generating a property summary
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, property_id):
        """
        Retrieve the summary for a property
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"PropertySummaryView: Fetching property with ID {property_id}")
            property_obj = get_object_or_404(Property, id=property_id)
            
            # Try to get an existing summary
            try:
                logger.info(f"PropertySummaryView: Looking for existing summary for property ID {property_id}")
                summary = PropertySummary.objects.get(property=property_obj)
                logger.info(f"PropertySummaryView: Found existing summary for property ID {property_id}")
                
                response_data = {
                    "summary": summary.summary_text,
                    "highlights": summary.highlights,
                    "generated_at": summary.updated_at,
                    "property_id": property_obj.id,  # Add property_id to the response
                    "model": summary.generate_version  # Add model info to the response
                }
                
                logger.info(f"PropertySummaryView: Returning response data: {response_data}")
                response_serializer = PropertySummaryResponseSerializer(response_data)
                return Response(response_serializer.data)
            except PropertySummary.DoesNotExist:
                # If no summary exists, generate one using our LLM service
                logger.info(f"PropertySummaryView: No existing summary found for property ID {property_id}, generating new one")
                
                try:
                    # Generate summary data using LLM service
                    summary_data = generate_property_summary(property_obj)
                    logger.info(f"PropertySummaryView: Successfully generated summary data for property ID {property_id}")
                    logger.info(f"PropertySummaryView: Generated summary data: {summary_data}")
                    
                    # Check if this is a fallback response
                    created_by = summary_data.get("created_by", "claude")
                    
                    # Ensure we have both summary and highlights fields
                    if "summary" not in summary_data:
                        logger.warning(f"Summary field missing from response for property ID {property_id}")
                        summary_data["summary"] = f"A {property_obj.property_type} in {property_obj.city} with {property_obj.bedroom_count} bedrooms."
                    
                    if "highlights" not in summary_data:
                        logger.warning(f"Highlights field missing from response for property ID {property_id}")
                        summary_data["highlights"] = [
                            f"{property_obj.bedroom_count} bedroom {property_obj.property_type}",
                            f"Located in {property_obj.city}",
                            "Modern amenities and comfort"
                        ]
                    
                    # If it's not a fallback response, save it to the database
                    if created_by != "fallback":
                        # Create a new PropertySummary object
                        summary = PropertySummary.objects.create(
                            property=property_obj,
                            summary_text=summary_data["summary"],
                            highlights=summary_data["highlights"],
                            generate_version="Claude-3-Sonnet-20240229"
                        )
                        
                        response_data = {
                            "summary": summary.summary_text,
                            "highlights": summary.highlights,
                            "generated_at": summary.created_at,
                            "property_id": property_obj.id,
                            "model": summary.generate_version
                        }
                    else:
                        # For fallback responses, don't save to database but return the data
                        logger.warning(f"PropertySummaryView: Generated a fallback response for property ID {property_id}")
                        response_data = {
                            "summary": summary_data["summary"],
                            "highlights": summary_data["highlights"],
                            "generated_at": timezone.now(),
                            "property_id": property_obj.id,
                            "model": "Claude-3-Sonnet-20240229"
                        }
                    
                    logger.info(f"PropertySummaryView: Returning summary response data: {response_data}")
                    response_serializer = PropertySummaryResponseSerializer(response_data)
                    return Response(response_serializer.data)
                except Exception as e:
                    logger.error(f"PropertySummaryView: Error generating summary for property ID {property_id}: {str(e)}", exc_info=True)
                    
                    # Create a fallback response with proper structure for the frontend
                    fallback_response = {
                        "summary": f"A lovely {property_obj.property_type} located in {property_obj.city}, {property_obj.country}. (Note: This is fallback data due to API error)",
                        "highlights": [
                            f"{property_obj.bedroom_count} bedroom accommodation",
                            f"Located in {property_obj.city}",
                            "Comfortable and convenient",
                            "FALLBACK DATA - API ERROR"
                        ],
                        "generated_at": timezone.now(),
                        "property_id": property_obj.id,
                        "model": "Claude-3-Sonnet-20240229"
                    }
                    
                    logger.info(f"PropertySummaryView: Returning fallback response: {fallback_response}")
                    response_serializer = PropertySummaryResponseSerializer(fallback_response)
                    return Response(response_serializer.data)
        except Exception as e:
            logger.error(f"PropertySummaryView: Unexpected error for property ID {property_id}: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RegenerateSummariesView(APIView):
    """
    API endpoint for regenerating all property summaries (admin only)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        """
        Regenerate all property summaries
        """
        properties = Property.objects.all()
        updated_count = 0
        
        for property_obj in properties:
            # Get summary from LLM
            summary_data = generate_property_summary(property_obj)
            
            # Update or create the summary
            summary, created = PropertySummary.objects.update_or_create(
                property=property_obj,
                defaults={
                    "summary_text": summary_data["summary"],
                    "highlights": summary_data["highlights"],
                    "generate_version": "Claude-3-Sonnet-20240229"
                }
            )
            
            updated_count += 1
        
        return Response({
            "detail": f"Regenerated {updated_count} property summaries."
        })

class UserPersonaView(APIView):
    """
    API endpoint for retrieving or generating a user persona
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        """
        Retrieve the persona for a user
        """
        # Ensure the user is requesting their own persona or is an admin
        if request.user.id != user_id and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to access this persona."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = get_object_or_404(User, id=user_id)
        
        # Try to get an existing persona
        try:
            persona = Persona.objects.get(user=user)
            response_serializer = PersonaResponseSerializer({
                "persona": persona.persona_data,
                "created_at": persona.created_at,
                "updated_at": persona.updated_at
            })
            return Response(response_serializer.data)
        except Persona.DoesNotExist:
            # If no persona exists, generate one using our LLM service
            persona_data = generate_user_persona(user)
            
            persona = Persona.objects.create(
                user=user,
                persona_type=Persona.PersonaType.USER,
                persona_data=persona_data,
                generate_version="Claude-3-Sonnet-20240229"
            )
            
            response_serializer = PersonaResponseSerializer({
                "persona": persona.persona_data,
                "created_at": persona.created_at,
                "updated_at": persona.updated_at
            })
            return Response(response_serializer.data)
            
    def delete(self, request, user_id):
        """
        Delete an existing persona to force regeneration
        """
        # Ensure the user is requesting their own persona or is an admin
        if request.user.id != user_id and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to delete this persona."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user = get_object_or_404(User, id=user_id)
        
        try:
            # Delete the existing persona if it exists
            persona = Persona.objects.get(user=user)
            persona.delete()
            
            # Generate a new persona immediately
            persona_data = generate_user_persona(user)
            
            persona = Persona.objects.create(
                user=user,
                persona_type=Persona.PersonaType.USER,
                persona_data=persona_data,
                generate_version="Claude-3-Sonnet-20240229"
            )
            
            response_serializer = PersonaResponseSerializer({
                "persona": persona.persona_data,
                "created_at": persona.created_at,
                "updated_at": persona.updated_at
            })
            return Response(response_serializer.data)
            
        except Persona.DoesNotExist:
            # If no persona exists, just generate a new one
            persona_data = generate_user_persona(user)
            
            persona = Persona.objects.create(
                user=user,
                persona_type=Persona.PersonaType.USER,
                persona_data=persona_data,
                generate_version="Claude-3-Sonnet-20240229"
            )
            
            response_serializer = PersonaResponseSerializer({
                "persona": persona.persona_data,
                "created_at": persona.created_at,
                "updated_at": persona.updated_at
            })
            return Response(response_serializer.data)

class PropertyPersonaView(APIView):
    """
    API endpoint for retrieving or generating a property persona
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, property_id):
        """
        Retrieve the persona for a property
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"PropertyPersonaView: Fetching property with ID {property_id}")
            property_obj = get_object_or_404(Property, id=property_id)
            
            # Try to get an existing persona
            try:
                logger.info(f"PropertyPersonaView: Looking for existing persona for property ID {property_id}")
                persona = Persona.objects.get(property=property_obj)
                logger.info(f"PropertyPersonaView: Found existing persona for property ID {property_id}")
                
                response_serializer = PersonaResponseSerializer({
                    "persona": persona.persona_data,
                    "created_at": persona.created_at,
                    "updated_at": persona.updated_at
                })
                return Response(response_serializer.data)
            except Persona.DoesNotExist:
                # If no persona exists, generate one using our LLM service
                logger.info(f"PropertyPersonaView: No existing persona found for property ID {property_id}, generating new one")
                
                try:
                    persona_data = generate_property_persona(property_obj)
                    logger.info(f"PropertyPersonaView: Successfully generated persona data for property ID {property_id}")
                    
                    persona = Persona.objects.create(
                        property=property_obj,
                        persona_type=Persona.PersonaType.PROPERTY,
                        persona_data=persona_data,
                        generate_version="Claude-3-Sonnet-20240229"
                    )
                    
                    response_serializer = PersonaResponseSerializer({
                        "persona": persona.persona_data,
                        "created_at": persona.created_at,
                        "updated_at": persona.updated_at
                    })
                    return Response(response_serializer.data)
                except Exception as e:
                    logger.error(f"PropertyPersonaView: Error generating persona for property ID {property_id}: {str(e)}", exc_info=True)
                    return Response(
                        {"detail": f"Error generating property persona: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        except Exception as e:
            logger.error(f"PropertyPersonaView: Unexpected error for property ID {property_id}: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserRecommendationsView(APIView):
    """
    API endpoint for generating property recommendations for a user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        """
        Generate property recommendations for a user
        """
        # Ensure the user is requesting their own recommendations or is an admin
        if request.user.id != user_id and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to access these recommendations."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = get_object_or_404(User, id=user_id)
        
        # Generate recommendations using our LLM service
        recommendations_data = generate_recommendations(user)
        
        # Store recommendations in the database
        recommendation = Recommendation.objects.create(
            user=user,
            generate_version="Claude-3-Sonnet-20240229"
        )
        
        # Create recommendation items
        for i, rec in enumerate(recommendations_data):
            property_obj = Property.objects.get(id=rec["property_id"])
            RecommendationItem.objects.create(
                recommendation=recommendation,
                property=property_obj,
                score=rec["match_score"],
                reasoning=", ".join(rec["match_reasons"]),
                rank=i + 1
            )
        
        # Format for response
        response_data = []
        for rec in recommendations_data:
            property_obj = Property.objects.get(id=rec["property_id"])
            response_data.append({
                "id": property_obj.id,
                "title": property_obj.title,
                "price_per_night": str(property_obj.base_price),
                "match_score": rec["match_score"],
                "match_reasons": rec["match_reasons"]
            })
        
        response_serializer = RecommendationResponseSerializer({
            "recommendations": response_data,
            "generated_at": timezone.now()
        })
        return Response(response_serializer.data)

class CurrentUserRecommendationsView(APIView):
    """
    API endpoint for generating property recommendations for the current authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Generate property recommendations for the current user
        """
        user = request.user
        
        # Check for existing recommendations less than 24 hours old
        recent_recommendation = Recommendation.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-created_at').first()
        
        # If recent recommendation exists, return it instead of generating new ones
        if recent_recommendation:
            # Format for response
            response_data = []
            for item in recent_recommendation.items.all().order_by('rank'):
                property_obj = item.property
                response_data.append({
                    "id": property_obj.id,
                    "title": property_obj.title,
                    "price_per_night": str(property_obj.base_price),
                    "match_score": item.score,
                    "match_reasons": item.reasoning.split(", ")
                })
            
            response_serializer = RecommendationResponseSerializer({
                "recommendations": response_data,
                "generated_at": recent_recommendation.created_at
            })
            return Response(response_serializer.data)
        
        # Generate new recommendations using our LLM service
        recommendations_data = generate_recommendations(user)
        
        # Store recommendations in the database
        recommendation = Recommendation.objects.create(
            user=user,
            generate_version="Claude-3-Sonnet-20240229"
        )
        
        # Create recommendation items
        for i, rec in enumerate(recommendations_data):
            property_obj = Property.objects.get(id=rec["property_id"])
            RecommendationItem.objects.create(
                recommendation=recommendation,
                property=property_obj,
                score=rec["match_score"],
                reasoning=", ".join(rec["match_reasons"]),
                rank=i + 1
            )
        
        # Format for response
        response_data = []
        for rec in recommendations_data:
            property_obj = Property.objects.get(id=rec["property_id"])
            response_data.append({
                "id": property_obj.id,
                "title": property_obj.title,
                "price_per_night": str(property_obj.base_price),
                "match_score": rec["match_score"],
                "match_reasons": rec["match_reasons"]
            })
        
        response_serializer = RecommendationResponseSerializer({
            "recommendations": response_data,
            "generated_at": timezone.now()
        })
        return Response(response_serializer.data)

# New management views for LLM services

class LLMProviderStatusView(APIView):
    """
    API endpoint for getting status information on LLM providers
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Get information about configured LLM providers and their status
        """
        from .services.llm_manager import llm_manager
        
        status_data = llm_manager.get_provider_status()
        
        return Response(status_data)

class LLMCacheStatsView(APIView):
    """
    API endpoint for viewing LLM cache statistics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Get detailed cache statistics
        """
        from .services.llm_manager import llm_manager
        
        cache_stats = llm_manager.get_cache_statistics()
        
        return Response(cache_stats)
    
    def delete(self, request):
        """
        Clear the LLM cache
        """
        from .services.llm_manager import llm_manager
        
        # Get days parameter if provided
        days = request.query_params.get('days')
        max_age_seconds = int(days) * 86400 if days else None
        
        result = llm_manager.clear_cache(max_age_seconds)
        
        return Response(result)

class LLMCacheSavingsView(APIView):
    """
    API endpoint for analyzing estimated cost savings from LLM caching
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Get estimated cost savings data from LLM caching
        """
        from .services.cache_analyzer import analyze_cache_savings
        
        savings_data = analyze_cache_savings()
        
        return Response({
            "total_estimated_savings": f"${round(sum(savings_data.get('provider_savings', {}).values()), 2)}",
            "savings_data": savings_data
        })
    
    def post(self, request):
        """
        Generate a savings chart and return the chart URL
        """
        from .services.cache_analyzer import generate_savings_chart
        import datetime
        
        # Generate a unique filename based on timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"cache_savings_{timestamp}.png"
        
        # Get the absolute path to the static directory
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'cache_charts')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate the chart
        filepath = os.path.join(static_dir, filename)
        generate_savings_chart(filepath)
        
        # Return the URL path to the chart
        chart_url = f"/static/cache_charts/{filename}"
        
        return Response({"chart_url": chart_url})

# LangChain recommendation views
from .services.simple_langchain_agent import get_recommendation_agent, SimpleRecommendationAgent


class ConversationalRecommendationsView(APIView):
    """
    API endpoint for getting conversational property recommendations for the current user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Generate initial recommendations for the current user based on their profile.
        """
        try:
            user_id = request.user.id
            query = request.query_params.get('query', None)
            
            # Get recommendation agent
            recommendation_agent = get_recommendation_agent()
            
            # Generate recommendations
            recommendations = recommendation_agent.generate_recommendations(user_id, query)
            
            return Response(recommendations, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error generating conversational recommendations: {str(e)}")
            return Response({
                "error": "Failed to generate recommendations",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Refine recommendations based on user feedback/follow-up questions.
        """
        try:
            user_id = request.user.id
            feedback = request.data.get('feedback', '')
            
            if not feedback:
                return Response({
                    "error": "Feedback is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get recommendation agent
            recommendation_agent = get_recommendation_agent()
            
            # Refine recommendations
            refined_recommendations = recommendation_agent.refine_recommendations(user_id, feedback)
            
            return Response(refined_recommendations, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error refining conversational recommendations: {str(e)}")
            return Response({
                "error": "Failed to refine recommendations",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """
        Clear the conversation history/memory for the current user.
        """
        try:
            # Get recommendation agent
            recommendation_agent = get_recommendation_agent()
            
            # Clear conversation history
            recommendation_agent.clear_conversation_history()
            
            return Response({
                "message": "Conversation history cleared successfully"
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
            return Response({
                "error": "Failed to clear conversation history",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminConversationalRecommendationsView(APIView):
    """
    Admin API endpoint for getting or refining conversational property recommendations for any user
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, user_id):
        """
        Generate initial recommendations for a specific user based on their profile.
        """
        try:
            user = get_object_or_404(User, id=user_id)
            query = request.query_params.get('query', None)
            
            # Get recommendation agent
            recommendation_agent = get_recommendation_agent()
            
            # Generate recommendations
            recommendations = recommendation_agent.generate_recommendations(user_id, query)
            
            return Response(recommendations, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                "error": f"User with ID {user_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating admin conversational recommendations: {str(e)}")
            return Response({
                "error": "Failed to generate recommendations",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, user_id):
        """
        Refine recommendations based on admin-provided feedback for a specific user.
        """
        try:
            user = get_object_or_404(User, id=user_id)
            feedback = request.data.get('feedback', '')
            
            if not feedback:
                return Response({
                    "error": "Feedback is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get recommendation agent
            recommendation_agent = get_recommendation_agent()
            
            # Refine recommendations
            refined_recommendations = recommendation_agent.refine_recommendations(user_id, feedback)
            
            return Response(refined_recommendations, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                "error": f"User with ID {user_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error refining admin conversational recommendations: {str(e)}")
            return Response({
                "error": "Failed to refine recommendations",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
