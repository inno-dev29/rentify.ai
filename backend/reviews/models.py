from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from properties.models import Property
from bookings.models import Booking
from users.models import User

class Review(models.Model):
    """
    Model for property reviews left by renters after a stay
    """
    # Relationships
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    
    # Rating details (1-5 scale)
    overall_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Overall rating from 1-5')
    )
    cleanliness_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Cleanliness rating from 1-5')
    )
    accuracy_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Accuracy rating from 1-5')
    )
    location_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Location rating from 1-5')
    )
    value_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Value rating from 1-5')
    )
    communication_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Communication rating from 1-5')
    )
    
    # Review content
    comment = models.TextField(help_text=_('Review text'))
    
    # Leaser response
    leaser_response = models.TextField(blank=True, null=True, help_text=_('Leaser response to the review'))
    response_date = models.DateTimeField(blank=True, null=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True, help_text=_('Is this review approved and visible'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        ordering = ['-created_at']
        # Ensure a user can only review a booking once
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'reviewer'],
                name='unique_review_per_booking'
            )
        ]
    
    def __str__(self):
        return f"Review for {self.property.title} by {self.reviewer.username}"
    
    def average_rating(self):
        """Calculate the average rating across all categories"""
        ratings = [
            self.overall_rating,
            self.cleanliness_rating,
            self.accuracy_rating,
            self.location_rating,
            self.value_rating,
            self.communication_rating
        ]
        return sum(ratings) / len(ratings)
    average_rating.short_description = _('Average Rating')

class ReviewImage(models.Model):
    """
    Images attached to reviews
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images')
    caption = models.CharField(max_length=200, blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Review Image')
        verbose_name_plural = _('Review Images')
        
    def __str__(self):
        return f"Image for review #{self.review.id}"
