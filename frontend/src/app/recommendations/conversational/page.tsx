'use client';

import { useEffect, useState } from 'react';
import { ConversationalRecommendations } from '@/components/LLM';
import { useAuth } from '@/app/context/AuthContext';
import { useRouter, useSearchParams } from 'next/navigation';

export default function ConversationalRecommendationsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('query') || undefined;
  
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login?redirect=/recommendations/conversational');
    }
  }, [isAuthenticated, isLoading, router]);
  
  if (isLoading) {
    return (
      <div className="container mx-auto p-4">
        <div className="flex justify-center items-center h-64">
          <p>Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8">Conversational Property Recommendations</h1>
      <p className="mb-6 text-gray-600">
        Tell our AI assistant what you're looking for in a property, and it will provide personalized recommendations 
        based on your preferences and our available listings. You can refine your search through natural conversation.
      </p>
      
      <ConversationalRecommendations initialQuery={initialQuery} />
    </div>
  );
} 