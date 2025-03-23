import logging
from django.core.management.base import BaseCommand
from properties.models import Property
from llm_services.services.llm_client import generate_property_summary, UnifiedLLMClient
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test property summary generation with Claude'

    def handle(self, *args, **options):
        # Print environment settings
        self.stdout.write(self.style.SUCCESS(f"DEBUG_LLM: {getattr(settings, 'DEBUG_LLM', False)}"))
        self.stdout.write(self.style.SUCCESS(f"DEFAULT_LLM_PROVIDER: {getattr(settings, 'DEFAULT_LLM_PROVIDER', 'claude')}"))
        self.stdout.write(self.style.SUCCESS(f"CLAUDE_API_KEY: {getattr(settings, 'CLAUDE_API_KEY', '')[:4]}...{getattr(settings, 'CLAUDE_API_KEY', '')[-4:] if len(getattr(settings, 'CLAUDE_API_KEY', '')) > 8 else ''}"))
        
        # Get a property
        property_obj = Property.objects.first()
        if not property_obj:
            self.stdout.write(self.style.ERROR("No properties found in the database"))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Testing with property: {property_obj.title} (ID: {property_obj.id})"))
        
        try:
            # Initialize a UnifiedLLMClient directly
            unified_client = UnifiedLLMClient(preferred_provider='claude')
            self.stdout.write(self.style.SUCCESS(f"Claude client initialized successfully: {unified_client.has_claude}"))
            
            # Test a simple prompt with Claude directly
            try:
                self.stdout.write(self.style.SUCCESS("Testing Claude client with a simple prompt..."))
                test_response = unified_client.generate_response(
                    system_prompt="You are a helpful assistant.",
                    user_prompt="Return only the word 'SUCCESS' if you receive this message.",
                    temperature=0.1,
                    max_tokens=10
                )
                self.stdout.write(self.style.SUCCESS(f"Claude test response: {test_response['content']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Claude test failed: {str(e)}"))
            
            # Generate property summary
            self.stdout.write(self.style.SUCCESS("Testing property summary generation..."))
            result = generate_property_summary(property_obj)
            
            # Print the result
            self.stdout.write(self.style.SUCCESS("Summary generation result:"))
            self.stdout.write(str(result))
            
            # Check for fallback response
            if result.get('created_by') == 'fallback':
                self.stdout.write(self.style.WARNING("⚠️ A fallback response was generated!"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ A real LLM-generated response was produced!"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}")) 