from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review-list'),
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('properties/<int:property_id>/', views.PropertyReviewListView.as_view(), name='property-review-list'),
    path('bookings/<int:booking_id>/', views.BookingReviewCreateView.as_view(), name='booking-review-create'),
    path('<int:review_id>/images/', views.ReviewImageListCreateView.as_view(), name='review-image-list-create'),
    path('<int:review_id>/images/<int:pk>/', views.ReviewImageDetailView.as_view(), name='review-image-detail'),
] 