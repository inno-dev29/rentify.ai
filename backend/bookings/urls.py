from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.BookingListCreateView.as_view(), name='booking-list-create'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('<int:pk>/status/', views.BookingStatusUpdateView.as_view(), name='booking-status-update'),
    # Keep for backwards compatibility but redirect to the endpoint in properties app in the future
    path('properties/<int:property_id>/availability/', views.PropertyAvailabilityView.as_view(), name='property-availability-legacy'),
] 