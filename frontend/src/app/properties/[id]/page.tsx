// Server component to handle params
import { Property } from '@/types/property';
import { propertyService } from '@/app/api/services/propertyService';
import PropertyDetailClient from './client';

// Server component to handle route params
export default async function PropertyDetailPage({ params }: { params: { id: string } }) {
  // Property ID from route params is already a string, no need to extract it
  const propertyId = params.id;
  
  try {
    // Pre-fetch the property data server-side
    const propertyData = await propertyService.getProperty(parseInt(propertyId));
    
    // Pass the data to the client component
    return <PropertyDetailClient propertyId={propertyId} initialProperty={propertyData} />;
  } catch (error) {
    console.error('Failed to fetch property details:', error);
    return <PropertyDetailClient propertyId={propertyId} initialProperty={null} error="Failed to load property details. Please try again later." />;
  }
} 