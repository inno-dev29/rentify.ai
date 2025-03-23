from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Review, ReviewImage

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 2
    readonly_fields = ('upload_date',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'reviewer', 'overall_rating', 'average_rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'overall_rating')
    search_fields = ('property__title', 'reviewer__username', 'comment', 'leaser_response')
    readonly_fields = ('created_at', 'updated_at', 'average_rating')
    inlines = [ReviewImageInline]
    
    fieldsets = (
        (_('Review Info'), {
            'fields': ('property', 'booking', 'reviewer', 'is_approved')
        }),
        (_('Ratings'), {
            'fields': ('overall_rating', 'cleanliness_rating', 'accuracy_rating', 
                      'location_rating', 'value_rating', 'communication_rating', 'average_rating')
        }),
        (_('Content'), {
            'fields': ('comment', 'leaser_response', 'response_date')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def average_rating(self, obj):
        return round(obj.average_rating, 2)
    average_rating.short_description = _('Average Rating')

@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('review', 'upload_date', 'caption')
    list_filter = ('upload_date',)
    search_fields = ('review__comment', 'caption', 'review__property__title')
    readonly_fields = ('upload_date',)
