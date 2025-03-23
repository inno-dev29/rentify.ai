from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PropertySummary, Persona, Recommendation, RecommendationItem

class RecommendationItemInline(admin.TabularInline):
    model = RecommendationItem
    extra = 0
    readonly_fields = ('score', 'rank')

@admin.register(PropertySummary)
class PropertySummaryAdmin(admin.ModelAdmin):
    list_display = ('property', 'generate_version', 'created_at', 'updated_at')
    search_fields = ('property__title', 'summary_text')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Property'), {
            'fields': ('property',)
        }),
        (_('Generated Content'), {
            'fields': ('summary_text', 'highlights')
        }),
        (_('Generation Info'), {
            'fields': ('generate_version', 'prompt_used')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'persona_type', 'user', 'property', 'generate_version', 'created_at')
    list_filter = ('persona_type', 'generate_version')
    search_fields = ('user__username', 'property__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Persona Type'), {
            'fields': ('persona_type', 'user', 'property')
        }),
        (_('Persona Data'), {
            'fields': ('persona_data',)
        }),
        (_('Generation Info'), {
            'fields': ('generate_version', 'prompt_used')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'generate_version', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RecommendationItemInline]
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Generation Info'), {
            'fields': ('generate_version', 'prompt_used')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RecommendationItem)
class RecommendationItemAdmin(admin.ModelAdmin):
    list_display = ('recommendation', 'property', 'rank', 'score')
    list_filter = ('rank',)
    search_fields = ('recommendation__user__username', 'property__title', 'reasoning')
