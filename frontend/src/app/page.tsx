'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Property, PropertyFilters } from '@/types/property';
import { propertyService, PropertyFilterParams } from './api/services/propertyService';
import { Button } from '@/components/ui/button';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { PropertyRecommendations } from '@/components/LLM';

export default function Home() {
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
      console.log('Fetching properties from API...');
      const data = await propertyService.getProperties();
      console.log('Properties data received:', data);
      
      // Check if the response contains a 'results' field (paginated response)
      const propertiesList = data.results || data;
      
      if (!propertiesList || propertiesList.length === 0) {
        console.warn('No properties found in the response');
      }
      
      setProperties(propertiesList || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch properties:', err);
      setError('Failed to load properties. Please try again later.');
      setProperties([]); // Ensure properties is set to an empty array on error
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
    const apiFilters: PropertyFilterParams = {};
    
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
      apiFilters.min_price = parseInt(filters.min_price);
    }
    
    if (filters.max_price) {
      apiFilters.max_price = parseInt(filters.max_price);
    }
    
    if (filters.bedroom_count) {
      apiFilters.min_bedrooms = parseInt(filters.bedroom_count);
    }
    
    if (filters.bathroom_count) {
      apiFilters.min_bathrooms = parseFloat(filters.bathroom_count);
    }
    
    console.log('Applying filters:', apiFilters);
    
    try {
      const data = await propertyService.getProperties(apiFilters);
      // Check if the response contains a 'results' field (paginated response)
      const propertiesList = data.results || data;
      setProperties(propertiesList);
      setError(null);
    } catch (err) {
      console.error('Failed to search properties:', err);
      setError('Failed to search properties. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <section className="bg-blue-600 text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold mb-6">Find Your Perfect Rental Property</h1>
          <p className="text-xl mb-8">Discover amazing properties for your next stay</p>
          
          <Card>
            <CardContent className="p-6">
              <form onSubmit={handleSearch}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <label htmlFor="city" className="block text-secondary">City</label>
                    <input
                      type="text"
                      id="city"
                      name="city"
                      value={filters.city}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                      placeholder="Enter city"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="country" className="block text-secondary">Country</label>
                    <input
                      type="text"
                      id="country"
                      name="country"
                      value={filters.country}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                      placeholder="Enter country"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="property_type" className="block text-secondary">Property Type</label>
                    <select
                      id="property_type"
                      name="property_type"
                      value={filters.property_type}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                    >
                      <option value="">All Types</option>
                      <option value="house">House</option>
                      <option value="apartment">Apartment</option>
                      <option value="condo">Condo</option>
                      <option value="villa">Villa</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <label htmlFor="min_price" className="block text-secondary">Min Price</label>
                    <input
                      type="number"
                      id="min_price"
                      name="min_price"
                      value={filters.min_price}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                      placeholder="Min $"
                      min="0"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="max_price" className="block text-secondary">Max Price</label>
                    <input
                      type="number"
                      id="max_price"
                      name="max_price"
                      value={filters.max_price}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                      placeholder="Max $"
                      min="0"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="bedroom_count" className="block text-secondary">Bedrooms</label>
                    <select
                      id="bedroom_count"
                      name="bedroom_count"
                      value={filters.bedroom_count}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                    >
                      <option value="">Any</option>
                      <option value="1">1+</option>
                      <option value="2">2+</option>
                      <option value="3">3+</option>
                      <option value="4">4+</option>
                      <option value="5">5+</option>
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="bathroom_count" className="block text-secondary">Bathrooms</label>
                    <select
                      id="bathroom_count"
                      name="bathroom_count"
                      value={filters.bathroom_count}
                      onChange={handleFilterChange}
                      className="w-full p-2 border rounded text-secondary"
                    >
                      <option value="">Any</option>
                      <option value="1">1+</option>
                      <option value="2">2+</option>
                      <option value="3">3+</option>
                      <option value="4">4+</option>
                    </select>
                  </div>
                </div>
                
                <div className="text-center">
                  <Button type="submit">
                    Search Properties
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </section>
      
      <section className="py-12">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold mb-8">Featured Properties</h2>
          
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
      </section>
      
      <section className="bg-gray-100 py-12">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">Why Choose Our Platform?</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <div className="text-primary text-4xl mb-4">🏠</div>
                <CardTitle>Verified Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-secondary">All our properties are verified and meet our quality standards.</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <div className="text-primary text-4xl mb-4">⭐</div>
                <CardTitle>Honest Reviews</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-secondary">Our reviews are from verified stays, ensuring honest feedback.</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <div className="text-primary text-4xl mb-4">🔒</div>
                <CardTitle>Secure Bookings</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-secondary">Book with confidence with our secure booking system.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
      
      {/* AI-Generated Recommendations Section - Only shown when user is logged in */}
      <section className="py-12 bg-gray-50 dark:bg-gray-800">
        <div className="container mx-auto px-4">
          <PropertyRecommendations limit={4} />
        </div>
      </section>
    </div>
  );
}
