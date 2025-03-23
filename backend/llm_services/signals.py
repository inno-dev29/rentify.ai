import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from properties.models import Property
from .models import Persona
from .services.llm_client import generate_property_persona

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Property)
def regenerate_property_persona(sender, instance, created, **kwargs):
    """
    Signal handler to regenerate property persona when a property is updated.
    
    This ensures that whenever a property's details are changed, the AI-generated
    persona will be refreshed to accurately reflect the current property information.
    
    Args:
        sender: The model class that sent the signal (Property)
        instance: The actual Property instance that was saved
        created: Boolean indicating if this is a new record
        kwargs: Additional keyword arguments
    """
    if not created:  # Only for updates, not for new properties
        try:
            # Check if a persona already exists for this property
            try:
                persona = Persona.objects.get(property=instance)
                logger.info(f"Regenerating persona for property ID {instance.id}: {instance.title}")
                
                # Generate new persona data
                persona_data = generate_property_persona(instance)
                
                # Update existing persona
                persona.persona_data = persona_data
                persona.generate_version = "Claude-3-Sonnet-20240229"  # Update the generator version if needed
                persona.save()
                
                logger.info(f"Successfully regenerated persona for property ID {instance.id}")
            except Persona.DoesNotExist:
                # No existing persona, no need to regenerate
                logger.info(f"No existing persona for property ID {instance.id}, skipping regeneration")
                pass
                
        except Exception as e:
            logger.error(f"Error regenerating property persona for ID {instance.id}: {str(e)}") 