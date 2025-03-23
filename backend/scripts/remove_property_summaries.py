#!/usr/bin/env python
"""
This script removes all LLM-generated content from the database, including:
- Property summaries
- Property personas
- User recommendations

Run with: python scripts/remove_property_summaries.py

Options:
--dry-run: Show what would be deleted without actually deleting
--summaries-only: Only delete property summaries
--personas-only: Only delete property personas
--recommendations-only: Only delete recommendations
--id: Delete content for a specific property ID only
"""

import os
import sys
import django
import argparse

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from llm_services.models import PropertySummary, Persona, Recommendation
from properties.models import Property

def remove_property_summaries(dry_run=False, property_id=None):
    """Remove property summaries from the database."""
    # Build the query
    query = PropertySummary.objects.all()
    
    if property_id:
        query = query.filter(property=property_id)
    
    # Get the count before deletion
    count = query.count()
    
    if count == 0:
        print("No property summaries found matching the criteria.")
        return
    
    # Print the summaries that would be deleted
    if dry_run:
        print(f"The following {count} property summaries would be deleted:")
        for summary in query:
            print(f"ID: {summary.id}, Property: {summary.property.id} ({summary.property.title})")
        print("\nThis was a dry run. No summaries were deleted.")
    else:
        # Perform the deletion
        print(f"Deleting {count} property summaries...")
        
        # Store property IDs to update llm_summary field
        property_ids = list(query.values_list('property_id', flat=True))
        
        # Delete the summaries
        query.delete()
        
        # Clear the llm_summary field in the Property model for these properties
        Property.objects.filter(id__in=property_ids).update(llm_summary=None)
        
        print(f"Successfully deleted {count} property summaries.")
        print(f"Also cleared the llm_summary field for {len(property_ids)} properties.")

def remove_property_personas(dry_run=False, property_id=None):
    """Remove property personas from the database."""
    # Build the query
    query = Persona.objects.all()
    
    if property_id:
        query = query.filter(property=property_id)
    
    # Get the count before deletion
    count = query.count()
    
    if count == 0:
        print("No property personas found matching the criteria.")
        return
    
    # Print the personas that would be deleted
    if dry_run:
        print(f"The following {count} property personas would be deleted:")
        for persona in query:
            property_info = "No property" if persona.property is None else f"Property: {persona.property.id} ({persona.property.title})"
            print(f"ID: {persona.id}, {property_info}")
        print("\nThis was a dry run. No personas were deleted.")
    else:
        # Perform the deletion
        print(f"Deleting {count} property personas...")
        
        # Delete the personas
        query.delete()
        
        print(f"Successfully deleted {count} property personas.")

def remove_recommendations(dry_run=False):
    """Remove recommendation records from the database."""
    # Build the query
    query = Recommendation.objects.all()
    
    # Get the count before deletion
    count = query.count()
    
    if count == 0:
        print("No recommendations found.")
        return
    
    # Print the recommendations that would be deleted
    if dry_run:
        print(f"The following {count} recommendations would be deleted:")
        for rec in query:
            user_info = "No user" if rec.user is None else f"User: {rec.user.username}"
            print(f"ID: {rec.id}, {user_info}, Items: {rec.items.count()}")
        print("\nThis was a dry run. No recommendations were deleted.")
    else:
        # Perform the deletion
        print(f"Deleting {count} recommendations...")
        
        # Delete the recommendations
        query.delete()
        
        print(f"Successfully deleted {count} recommendations.")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Remove LLM-generated content from the database.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--summaries-only', action='store_true', help='Only delete property summaries')
    parser.add_argument('--personas-only', action='store_true', help='Only delete property personas')
    parser.add_argument('--recommendations-only', action='store_true', help='Only delete recommendations')
    parser.add_argument('--id', type=int, help='Delete content for a specific property ID only')
    
    args = parser.parse_args()
    
    # If no specific content type is selected, delete all types
    delete_all = not (args.summaries_only or args.personas_only or args.recommendations_only)
    
    # Delete property summaries
    if delete_all or args.summaries_only:
        remove_property_summaries(dry_run=args.dry_run, property_id=args.id)
    
    # Delete property personas
    if delete_all or args.personas_only:
        remove_property_personas(dry_run=args.dry_run, property_id=args.id)
    
    # Delete recommendations
    if delete_all or args.recommendations_only:
        if args.id:
            print("Note: The --id flag doesn't apply to recommendations since they are not property-specific.")
        remove_recommendations(dry_run=args.dry_run)

if __name__ == "__main__":
    main() 