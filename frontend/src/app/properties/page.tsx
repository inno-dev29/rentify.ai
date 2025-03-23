'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Property, PropertyFilters } from '@/types/property';
import { propertyService } from '@/app/api/services/propertyService';
import { Button } from '@/components/ui/button';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<PropertyFilters>({
    city: '',
    country: '',
    property_type: '',
    min_price: '',
    max_price: '',
    bedroom_count: '',
    bathroom_count: ''
  });

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    setLoading(true);
    try {
      console.log('Fetching properties from: /properties/');
      const data = await propertyService.getProperties();
      console.log('Successfully fetched properties:', data);
      // Handle paginated response
      setProperties(data.results || data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch properties:', err);
      // Display more detailed error information
      if (err instanceof Error) {
        setError(`Failed to load properties: ${err.message}`);
      } else {
        setError('Failed to load properties. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Convert the form filters to the format expected by the propertyService
    const apiFilters: any = {};
    
    if (filters.city || filters.country) {
      // Combine city and country into location if either is provided
      const locationParts = [];
      if (filters.city) locationParts.push(filters.city);
      if (filters.country) locationParts.push(filters.country);
      apiFilters.location = locationParts.join(', ');
    }
    
    if (filters.property_type) {
      apiFilters.type = filters.property_type;
    }
    
    if (filters.min_price) {
      apiFilters.min_price = filters.min_price;
    }
    
    if (filters.max_price) {
      apiFilters.max_price = filters.max_price;
    }
    
    if (filters.bedroom_count) {
      apiFilters.min_bedrooms = filters.bedroom_count;
    }
    
    if (filters.bathroom_count) {
      apiFilters.min_bathrooms = filters.bathroom_count;
    }
    
    console.log('Applying filters:', apiFilters);
    
    try {
      const data = await propertyService.getProperties(apiFilters);
      // Handle paginated response
      setProperties(data.results || data);
      setError(null);
    } catch (err) {
      console.error('Failed to search properties:', err);
      setError('Failed to search properties. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">All Properties</h1>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Filter Properties</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="city" className="block text-sm font-medium text-secondary mb-1">
                City
              </label>
              <input
                type="text"
                id="city"
                name="city"
                value={filters.city}
                onChange={handleFilterChange}
                className="w-full p-2 border rounded-md text-secondary"
                placeholder="Enter city"
              />
            </div>
            
            <div>
              <label htmlFor="country" className="block text-sm font-medium text-secondary mb-1">
                Country
              </label>
              <input
                type="text"
                id="country"
                name="country"
                value={filters.country}
                onChange={handleFilterChange}
                className="w-full p-2 border rounded-md text-secondary"
                placeholder="Enter country"
              />
            </div>
            
            <div>
              <label htmlFor="property_type" className="block text-sm font-medium text-secondary mb-1">
                Property Type
              </label>
              <select
                id="property_type"
                name="property_type"
                value={filters.property_type}
                onChange={handleFilterChange}
                className="w-full p-2 border rounded-md text-secondary"
              >
                <option value="">All Types</option>
                <option value="house">House</option>
                <option value="apartment">Apartment</option>
                <option value="condo">Condo</option>
                <option value="villa">Villa</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="min_price" className="block text-sm font-medium text-secondary mb-1">
                Min Price ($/night)
              </label>
              <input
                type="number"
                id="min_price"
                name="min_price"
                value={filters.min_price}
                onChange={handleFilterChange}
                className="w-full p-2 border rounded-md text-secondary"
                placeholder="Min price"
                min="0"
              />
            </div>
            
            <div>
              <label htmlFor="max_price" className="block text-sm font-medium text-secondary mb-1">
                Max Price ($/night)
              </label>
              <input
                type="number"
                id="max_price"
                name="max_price"
                value={filters.max_price}
                onChange={handleFilterChange}
                className="w-full p-2 border rounded-md text-secondary"
                placeholder="Max price"
                min="0"
              />
            </div>
            
            <div className="flex items-end">
              <Button type="submit" className="w-full">
                Apply Filters
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      ) : properties.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 text-lg">No properties found matching your criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {properties.map(property => (
            <Card key={property.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <div className="relative h-48">
                {property.primary_image_url ? (
                  <Image
                    src={property.primary_image_url}
                    alt={property.title}
                    fill
                    className="object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-400">No image available</span>
                  </div>
                )}
              </div>
              
              <CardHeader className="pb-0">
                <CardTitle className="text-lg">{property.title}</CardTitle>
                <CardDescription>{property.city}, {property.country}</CardDescription>
              </CardHeader>
              
              <CardContent>
                <p className="text-secondary mb-4 line-clamp-2">{property.description}</p>
                
                <div className="flex justify-between items-center">
                  <div className="text-sm text-secondary">
                    <span className="mr-2">{property.bedroom_count} {property.bedroom_count === 1 ? 'Bedroom' : 'Bedrooms'}</span>
                    <span className="mr-2">•</span>
                    <span>{property.bathroom_count} {property.bathroom_count === 1 ? 'Bathroom' : 'Bathrooms'}</span>
                  </div>
                  <div className="text-primary font-semibold">${property.base_price}/night</div>
                </div>
              </CardContent>
              
              <CardFooter>
                <Button asChild className="w-full">
                  <Link href={`/properties/${property.id}`}>
                    View Details
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
} 