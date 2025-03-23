import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // Properly await params before using it (fixing the warning)
  const id = params.id;
  
  console.log(`[API Route] Proxying request for property ID: ${id} to ${API_BASE_URL}/llm/properties/${id}/summary/`);
  
  try {
    // Build headers object
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    // Add Authorization header if present in the request
    const authHeader = request.headers.get('Authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    // Forward the request to the backend API
    const response = await fetch(`${API_BASE_URL}/llm/properties/${id}/summary/`, {
      headers,
    });

    if (!response.ok) {
      // If the backend returns an error, return it to the client
      return NextResponse.json(
        { error: `Error fetching property summary: ${response.statusText}` },
        { status: response.status }
      );
    }

    // Parse the JSON response from the backend
    const data = await response.json();
    
    console.log('Property summary proxied through Next.js API route:', data);
    
    // Return the data to the client
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying property summary request:', error);
    return NextResponse.json(
      { error: 'Failed to fetch property summary' },
      { status: 500 }
    );
  }
} 