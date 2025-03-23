// Types for property-related entities

export interface Amenity {
  id: number;
  name: string;
  description?: string;
}

export interface PropertyImage {
  id: number;
  image_url: string;
  is_primary: boolean;
  property_id: number;
}

export interface Property {
  id: number;
  title: string;
  description: string;
  property_type: string;
  base_price: number;
  cleaning_fee: number;
  bedroom_count: number;
  bathroom_count: number;
  max_guests: number;
  city: string;
  country: string;
  address: string;
  is_active: boolean;
  amenities: Amenity[];
  images: PropertyImage[];
  primary_image_url?: string;
  created_at: string;
  leaser_id?: number;
  leaser?: {
    id: number;
    username: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    user_type?: string;
    // Other user properties
    [key: string]: any;
  };
}

export interface PropertyFilters {
  city?: string;
  country?: string;
  property_type?: string;
  min_price?: string;
  max_price?: string;
  bedroom_count?: string;
  bathroom_count?: string;
}

export interface PropertySummary {
  id?: number;
  property_id: number;
  summary: string;
  highlights: string[];
  generated_at: string;
  model?: string;
  created_by?: string;
}

// Types for AI-generated property personas
export interface PropertyPersona {
  property_id: number;
  ideal_guests: {
    demographics: string[];
    traveler_types: string[];
  };
  atmosphere: {
    overall_vibe: string;
    descriptors: string[];
  };
  use_cases: {
    primary: string[];
    secondary: string[];
  };
  unique_attributes: {
    key_selling_points: string[];
    stand_out_amenities: string[];
  };
  market_position: {
    property_class: string;
    comparable_to: string[];
  };
  neighborhood_vibe?: string;
  generated_at: string;
  model?: string;
  created_by?: string;
}

// Types for user recommendations
export interface PropertyRecommendation {
  property_id: number;
  title?: string;
  property_type?: string;
  city?: string;
  country?: string;
  base_price?: number;
  bedroom_count?: number;
  bathroom_count?: number;
  primary_image_url?: string;
  match_score: number;
  match_reasons: string[];
}

export interface UserRecommendations {
  user_id?: number;
  recommendations: PropertyRecommendation[];
  generated_at: string;
  model?: string;
  error_message?: string;
}

// Type for user personas
export interface UserPersona {
  user_id: number;
  preferences: {
    property_types?: string[];
    locations?: string[];
    amenities?: string[];
    price_range?: string;
    travel_style?: string[];
  };
  travel_habits?: {
    typical_group_size?: string;
    typical_stay_length?: string;
    booking_frequency?: string;
    planning_style?: string;
  };
  interests?: string[];
  generated_at: string;
  model?: string;
  created_by?: string;
}

// Type for conversational property recommendations (LangChain)
export interface ConversationalPropertyRecommendation {
  property_id: number;
  highlights: string;
}

export interface ConversationalRecommendations {
  personalized_explanation: string;
  properties: ConversationalPropertyRecommendation[];
  follow_up_questions: string[];
  error_message?: string;
} 