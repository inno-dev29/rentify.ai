from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Property, PropertyImage, Amenity

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    readonly_fields = ('upload_date',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'leaser', 'property_type', 'city', 'country', 'status', 'bedroom_count', 'bathroom_count', 'base_price')
    list_filter = ('property_type', 'status', 'city', 'country', 'bedroom_count')
    search_fields = ('title', 'description', 'address_line1', 'city', 'country', 'leaser__username')
    filter_horizontal = ('amenities',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PropertyImageInline]
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('title', 'description', 'leaser', 'property_type', 'status')
        }),
        (_('Location'), {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude')
        }),
        (_('Property Details'), {
            'fields': ('bedroom_count', 'bathroom_count', 'max_guests', 'square_feet', 'amenities')
        }),
        (_('Pricing'), {
            'fields': ('base_price', 'cleaning_fee', 'service_fee', 'extra_guest_fee', 'min_nights')
        }),
        (_('Rules and Policies'), {
            'fields': ('house_rules', 'cancellation_policy', 'check_in_time', 'check_out_time')
        }),
        (_('LLM Content'), {
            'fields': ('llm_summary',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'upload_date', 'caption')
    list_filter = ('is_primary', 'upload_date')
    search_fields = ('property__title', 'caption')
    readonly_fields = ('upload_date',)
