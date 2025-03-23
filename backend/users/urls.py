from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('me/', views.UserProfileView.as_view(), name='user-profile'),
    path('register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
] 