export interface ProcessedImage {
  // File Information
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  created_date: string;
  modified_date: string;
  thumbnail_path: string;
  drive_file_id: string;

  // AI-Extracted Visual Metadata
  primary_subject: string;
  visual_quality: number; // 1-5

  // People & Setting
  has_people: boolean;
  people_count: 'none' | '1-2' | '3-5' | '6-10' | '10+';
  is_indoor: boolean;

  // Activity Classification
  activity_tags: ActivityTag[];

  // Contextual Information
  season: 'spring' | 'summer' | 'fall' | 'winter' | 'unclear';
  time_of_day: 'morning' | 'midday' | 'evening' | 'unclear';
  mood_energy: string;
  color_palette: string;
  notes: string;

  // Marketing & Social Media Suitability
  social_media_score: number; // 1-5
  social_media_reason: string;
  marketing_score: number; // 1-5
}

export type ActivityTag = 
  | 'gardening'
  | 'harvesting'
  | 'education'
  | 'construction'
  | 'maintenance'
  | 'cooking'
  | 'celebration'
  | 'children'
  | 'animals'
  | 'landscape'
  | 'tools'
  | 'produce';

export interface SearchFilters {
  query: string;
  visualQuality: [number, number];
  hasPeople?: boolean;
  peopleCount: string[];
  isIndoor?: boolean;
  activityTags: ActivityTag[];
  season: string[];
  timeOfDay: string[];
  socialMediaScore: [number, number];
  marketingScore: [number, number];
}