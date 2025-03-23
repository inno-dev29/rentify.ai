from django.urls import path
from . import views
from bookings.views import PropertyAvailabilityView, PropertyBookingsView

app_name = 'properties'

urlpatterns = [
    path('', views.PropertyListCreateView.as_view(), name='property-list-create'),
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='property-detail'),
    path('<int:property_id>/images/', views.PropertyImageListCreateView.as_view(), name='property-image-list-create'),
    path('<int:property_id>/images/<int:pk>/', views.PropertyImageDetailView.as_view(), name='property-image-detail'),
    path('amenities/', views.AmenityListView.as_view(), name='amenity-list'),
    path('<int:property_id>/availability/', PropertyAvailabilityView.as_view(), name='property-availability'),
    path('<int:property_id>/bookings/', PropertyBookingsView.as_view(), name='property-bookings'),
] 