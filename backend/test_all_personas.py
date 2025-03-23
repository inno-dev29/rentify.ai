import os
import json
import logging
import time
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
import django
django.setup()

from properties.models import Property
from llm_services.services.llm_client import generate_property_persona

def test_all_property_personas():
    """Test property persona generation for all properties"""
    # Get all properties
    properties = Property.objects.all()
    logger.info(f"Testing property persona generation for {len(properties)} properties")
    
    results = {
        "total": len(properties),
        "successful": 0,
        "failed": 0,
        "generation_methods": {
            "claude": 0,
            "claude-fixed": 0,
            "regex-extraction": 0,
            "fallback": 0
        }
    }
    
    # Process each property
    for i, prop in enumerate(properties):
        logger.info(f"Processing property {i+1}/{len(properties)}: {prop.title} (ID: {prop.id})")
        
        try:
            start_time = time.time()
            persona = generate_property_persona(prop)
            duration = time.time() - start_time
            
            # Check result
            if persona:
                results["successful"] += 1
                
                # Record generation method
                generation_method = persona.get("created_by", "unknown")
                if generation_method in results["generation_methods"]:
                    results["generation_methods"][generation_method] += 1
                else:
                    results["generation_methods"][generation_method] = 1
                
                logger.info(f"✅ Success ({generation_method}) in {duration:.2f}s - " +
                           f"Demographics: {persona['ideal_guests']['demographics'][:2]}...")
            else:
                results["failed"] += 1
                logger.error(f"❌ Failed: result is None")
        
        except Exception as e:
            results["failed"] += 1
            logger.error(f"❌ Failed with error: {str(e)}")
    
    # Print summary
    logger.info("\n=== SUMMARY ===")
    logger.info(f"Total properties processed: {results['total']}")
    logger.info(f"Successful: {results['successful']} ({results['successful']/results['total']*100:.1f}%)")
    logger.info(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    logger.info("\nGeneration methods:")
    for method, count in results["generation_methods"].items():
        percentage = count / results["successful"] * 100 if results["successful"] > 0 else 0
        logger.info(f"  - {method}: {count} ({percentage:.1f}%)")
    
    return results

if __name__ == "__main__":
    results = test_all_property_personas()
    print("\nTest completed successfully.") 