from django.urls import path
from . import views

app_name = 'llm_services'

urlpatterns = [
    # Property summaries
    path('properties/<int:property_id>/summary/', views.PropertySummaryView.as_view(), name='property-summary'),
    path('admin/regenerate-summaries/', views.RegenerateSummariesView.as_view(), name='regenerate-summaries'),
    
    # Personas
    path('users/<int:user_id>/persona/', views.UserPersonaView.as_view(), name='user-persona'),
    path('properties/<int:property_id>/persona/', views.PropertyPersonaView.as_view(), name='property-persona'),
    
    # Recommendations
    path('users/<int:user_id>/recommendations/', views.UserRecommendationsView.as_view(), name='user-recommendations'),
    # New endpoint for current user recommendations
    path('users/me/recommendations/', views.CurrentUserRecommendationsView.as_view(), name='current-user-recommendations'),
    
    # LLM Service Management
    path('providers/status/', views.LLMProviderStatusView.as_view(), name='provider-status'),
    path('cache/stats/', views.LLMCacheStatsView.as_view(), name='cache-stats'),
    path('cache/savings/', views.LLMCacheSavingsView.as_view(), name='cache-savings'),
    
    # New LangChain-powered recommendation endpoints
    path('recommendations/conversational/', views.ConversationalRecommendationsView.as_view(), name='conversational-recommendations'),
    path('admin/user/<int:user_id>/conversational-recommendations/', views.AdminConversationalRecommendationsView.as_view(), name='admin-conversational-recommendations'),
] 