'use client';

import React, { useState, useEffect } from 'react';
import { llmService } from '@/app/api/services/llmService';
import { ConversationalRecommendations } from '@/types/property';
import { useAuth } from '@/app/context/AuthContext';
import { useRouter } from 'next/navigation';

// Import UI components individually since there's no index.ts
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface ConversationalRecommendationsProps {
  initialQuery?: string;
}

const ConversationalRecommendationsComponent: React.FC<ConversationalRecommendationsProps> = ({ 
  initialQuery 
}) => {
  const [recommendations, setRecommendations] = useState<ConversationalRecommendations | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<string>(initialQuery || '');
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  // Fetch initial recommendations
  useEffect(() => {
    if (isAuthenticated) {
      fetchRecommendations(initialQuery);
    }
  }, [isAuthenticated, initialQuery]);

  const fetchRecommendations = async (userQuery?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await llmService.getConversationalRecommendations(userQuery);
      setRecommendations(data);
      
      if (userQuery) {
        setConversationHistory(prev => [...prev, `You: ${userQuery}`]);
      }
      
    } catch (err) {
      console.error('Error fetching conversational recommendations:', err);
      setError('Failed to load recommendations. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefinement = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await llmService.refineConversationalRecommendations(query);
      setRecommendations(data);
      setConversationHistory(prev => [...prev, `You: ${query}`]);
      setQuery('');
    } catch (err) {
      console.error('Error refining recommendations:', err);
      setError('Failed to refine recommendations. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const resetConversation = async () => {
    setLoading(true);
    try {
      await llmService.clearConversationHistory();
      setConversationHistory([]);
      setRecommendations(null);
      fetchRecommendations();
    } catch (err) {
      console.error('Error clearing conversation history:', err);
      setError('Failed to reset conversation. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handlePropertyClick = (propertyId: number) => {
    router.push(`/properties/${propertyId}`);
  };

  if (!isAuthenticated) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center">Please sign in to get personalized property recommendations.</p>
        </CardContent>
        <CardFooter>
          <Button onClick={() => router.push('/login')} className="w-full">Sign In</Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-bold">Personalized Property Recommendations</h2>
          <p className="text-sm text-gray-500">Powered by AI to match your preferences</p>
        </CardHeader>
        
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-[20px] w-full" />
              <Skeleton className="h-[100px] w-full" />
              <Skeleton className="h-[20px] w-full" />
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 rounded-md text-red-500">
              {error}
            </div>
          ) : recommendations ? (
            <div className="space-y-4">
              {/* Conversation History */}
              {conversationHistory.length > 0 && (
                <div className="bg-gray-50 p-3 rounded-md max-h-40 overflow-y-auto">
                  {conversationHistory.map((message, index) => (
                    <p key={index} className="text-sm mb-2">{message}</p>
                  ))}
                  {recommendations.personalized_explanation && (
                    <p className="text-sm mb-2 text-blue-600">AI: {recommendations.personalized_explanation}</p>
                  )}
                </div>
              )}
              
              {/* Recommendations */}
              <div>
                {!conversationHistory.length && recommendations.personalized_explanation && (
                  <p className="mb-4">{recommendations.personalized_explanation}</p>
                )}
                
                <h3 className="font-semibold mb-2">Recommended Properties:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendations.properties.map((property) => (
                    <Card key={property.property_id} className="cursor-pointer hover:shadow-md transition-shadow" 
                          onClick={() => handlePropertyClick(property.property_id)}>
                      <CardContent className="p-4">
                        <h4 className="font-medium">Property #{property.property_id}</h4>
                        <p className="text-sm mt-2">{property.highlights}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
              
              {/* Follow-up Questions - Reformatted as direct input suggestions */}
              {recommendations.follow_up_questions && recommendations.follow_up_questions.length > 0 ? (
                <div className="bg-gray-50 p-4 rounded-md mt-4">
                  <h3 className="font-semibold mb-2">Example queries you can type:</h3>
                  <div className="space-y-2">
                    {recommendations.follow_up_questions.map((question, index) => {
                      // Convert questions to direct input statements
                      let inputSuggestion = question
                        .replace("Are you interested in", "I'm interested in")
                        .replace("Would you like", "I'd like")
                        .replace("Do you prefer", "I prefer")
                        .replace("Are you looking for", "I'm looking for")
                        .replace("?", "");
                      
                      return (
                        <p key={index} className="text-sm text-gray-700">
                          • "{inputSuggestion}"
                        </p>
                      );
                    })}
                  </div>
                  <p className="text-xs text-gray-500 mt-3">Type one of these sample inputs or describe your preferences in your own words.</p>
                </div>
              ) : (
                <div className="mt-4">
                  <p className="text-sm text-gray-600 italic">Based on your history, we've made recommendations that match your preferences. Tell us more if you're looking for something specific.</p>
                </div>
              )}
            </div>
          ) : (
            <p>Start a conversation to get personalized property recommendations.</p>
          )}
        </CardContent>
        
        <CardFooter className="flex flex-col space-y-3">
          <div className="flex w-full gap-2">
            <input
              type="text"
              value={query}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
              placeholder="Type 'I'm interested in...' or describe your preferences"
              className="flex-1 rounded border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
              onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleRefinement()}
            />
            <Button onClick={handleRefinement} disabled={loading || !query.trim()}>
              {loading ? 'Loading...' : 'Send'}
            </Button>
          </div>
          
          {conversationHistory.length > 0 && (
            <Button variant="outline" onClick={resetConversation} disabled={loading}>
              Start New Conversation
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
};

export default ConversationalRecommendationsComponent; 