from django.db import models
from django.utils.translation import gettext_lazy as _
from properties.models import Property
from users.models import User

class PropertySummary(models.Model):
    """
    Model to store LLM-generated property summaries
    """
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='ai_summary')
    summary_text = models.TextField(help_text=_('LLM-generated property summary'))
    highlights = models.JSONField(default=list, blank=True, help_text=_('Key property highlights'))
    
    # Generation info
    generate_version = models.CharField(max_length=50, help_text=_('Version of the summary generator'))
    prompt_used = models.TextField(blank=True, null=True, help_text=_('The prompt used to generate this summary'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Property Summary')
        verbose_name_plural = _('Property Summaries')
    
    def __str__(self):
        return f"Summary for {self.property.title}"

class Persona(models.Model):
    """
    Model for LLM-generated personas for users or properties
    """
    class PersonaType(models.TextChoices):
        USER = 'user', _('User Persona')
        PROPERTY = 'property', _('Property Persona')
    
    # Persona can be linked to either a user or a property (but not both)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personas', null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='personas', null=True, blank=True)
    
    # Persona data
    persona_type = models.CharField(max_length=10, choices=PersonaType.choices)
    persona_data = models.JSONField(help_text=_('Persona characteristics and information'))
    
    # Generation info
    generate_version = models.CharField(max_length=50, help_text=_('Version of the persona generator'))
    prompt_used = models.TextField(blank=True, null=True, help_text=_('The prompt used to generate this persona'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Persona')
        verbose_name_plural = _('Personas')
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Check that a Persona is only associated with either a user or a property, not both or neither
        if self.persona_type == self.PersonaType.USER and (self.property is not None or self.user is None):
            raise ValidationError(_('User personas must be linked to a user and not a property'))
        if self.persona_type == self.PersonaType.PROPERTY and (self.property is None or self.user is not None):
            raise ValidationError(_('Property personas must be linked to a property and not a user'))
    
    def __str__(self):
        if self.persona_type == self.PersonaType.USER:
            return f"Persona for user {self.user.username}"
        else:
            return f"Persona for property {self.property.title}"
            
class Recommendation(models.Model):
    """
    Model for storing property recommendations for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    properties = models.ManyToManyField(Property, through='RecommendationItem')
    
    # Generation info
    generate_version = models.CharField(max_length=50, help_text=_('Version of the recommendation engine'))
    prompt_used = models.TextField(blank=True, null=True, help_text=_('The prompt used to generate recommendations'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Recommendation')
        verbose_name_plural = _('Recommendations')
    
    def __str__(self):
        return f"Recommendations for {self.user.username}"

class RecommendationItem(models.Model):
    """
    Junction model for recommendations with additional data
    """
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='items')
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    score = models.FloatField(help_text=_('Recommendation score (higher is better)'))
    reasoning = models.TextField(help_text=_('Why this property was recommended'))
    rank = models.PositiveIntegerField(help_text=_('Ranking position in recommendations'))
    
    class Meta:
        verbose_name = _('Recommendation Item')
        verbose_name_plural = _('Recommendation Items')
        ordering = ['rank']
        unique_together = [['recommendation', 'property']]
    
    def __str__(self):
        return f"Recommendation of {self.property.title} for {self.recommendation.user.username}"
