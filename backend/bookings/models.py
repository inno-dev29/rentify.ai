from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from properties.models import Property

class Booking(models.Model):
    """
    Model to represent property bookings/reservations
    """
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')  # Waiting for leaser approval
        CONFIRMED = 'confirmed', _('Confirmed')  # Approved by leaser, payment processed
        CANCELLED = 'cancelled', _('Cancelled')  # Cancelled by renter or leaser
        COMPLETED = 'completed', _('Completed')  # Stay has been completed
        REJECTED = 'rejected', _('Rejected')  # Rejected by leaser
    
    # Relationships
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    start_date = models.DateField()
    end_date = models.DateField()
    guests_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    
    # Financial details
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text=_('Total booking price'))
    base_price_total = models.DecimalField(max_digits=10, decimal_places=2, help_text=_('Base price subtotal'))
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    extra_guest_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Payment information
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True, help_text=_('Payment processor ID'))
    
    # Additional details
    special_requests = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    leaser_notes = models.TextField(blank=True, null=True, help_text=_('Private notes for the leaser'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        ordering = ['-start_date']
        # Ensure one property can't be double-booked for overlapping dates
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            )
        ]
    
    def __str__(self):
        return f"{self.property.title} - {self.start_date} to {self.end_date}"
    
    def duration_nights(self):
        """Calculate the number of nights for this booking"""
        return (self.end_date - self.start_date).days
    duration_nights.short_description = _('Nights')
    
    def is_active(self):
        """Check if booking is currently active (confirmed and not completed)"""
        return self.status == self.BookingStatus.CONFIRMED
    
    def is_upcoming(self):
        """Check if booking is upcoming"""
        from django.utils import timezone
        return self.status == self.BookingStatus.CONFIRMED and self.start_date > timezone.now().date()
    
    def is_past(self):
        """Check if booking is in the past"""
        from django.utils import timezone
        return self.end_date < timezone.now().date()
