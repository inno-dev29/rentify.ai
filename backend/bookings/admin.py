from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'renter', 'start_date', 'end_date', 'status', 'guests_count', 'total_price', 'is_paid')
    list_filter = ('status', 'is_paid', 'start_date', 'end_date')
    search_fields = ('property__title', 'renter__username', 'renter__email', 'special_requests')
    readonly_fields = ('created_at', 'updated_at', 'duration_nights')
    
    fieldsets = (
        (_('Booking Details'), {
            'fields': ('property', 'renter', 'start_date', 'end_date', 'guests_count', 'status', 'duration_nights')
        }),
        (_('Financial Details'), {
            'fields': ('total_price', 'base_price_total', 'cleaning_fee', 'service_fee', 'extra_guest_fee')
        }),
        (_('Payment Info'), {
            'fields': ('is_paid', 'payment_method', 'payment_id')
        }),
        (_('Additional Details'), {
            'fields': ('special_requests', 'cancellation_reason', 'leaser_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_nights(self, obj):
        return obj.duration_nights
    duration_nights.short_description = _('Nights')
