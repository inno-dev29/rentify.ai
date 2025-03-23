from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model with additional fields for rentify.ai.
    """
    
    class UserType(models.TextChoices):
        LEASER = 'leaser', _('Leaser')  # Property owners/landlords
        RENTER = 'renter', _('Renter')  # Tenants/Guests
        ADMIN = 'admin', _('Administrator')  # System administrators
    
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.RENTER,
        help_text=_('Type of user account')
    )
    
    phone = models.CharField(max_length=20, blank=True, null=True, help_text=_('Contact phone number'))
    profile_image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text=_('User bio/description'))
    
    # Verification status
    is_verified = models.BooleanField(default=False, help_text=_('Email verification status'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return self.username

class UserProfile(models.Model):
    """
    Extended profile information for users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Address information
    address_line1 = models.CharField(max_length=100, blank=True, null=True)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    
    # Preferences
    preferred_currency = models.CharField(max_length=3, default='USD')
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    # For leasers
    business_name = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    # For renters
    payment_methods = models.JSONField(default=list, blank=True)
    
    # Travel preferences
    travel_preferences = models.TextField(blank=True, null=True, help_text="User's travel preferences in their own words")
    
    def __str__(self):
        return f"Profile for {self.user.username}"
