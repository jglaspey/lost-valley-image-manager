export interface ProcessedImage {
  // File Information
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  created_date: string;
  modified_date: string;
  thumbnail_path: string;
  drive_file_id: string;
  drive_view_url: string;
  drive_download_url: string;
  processing_status: 'pending' | 'in_progress' | 'completed' | 'failed';
  processed_at: string | null;
  error_message?: string;

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
  marketing_use: string;
  
  // Metadata tracking
  extracted_at: string;
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

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface ImageSearchResponse {
  images: ProcessedImage[];
  pagination: PaginationInfo;
  filters?: SearchFilters;
}

export interface StatsResponse {
  fileStats: {
    total_files: number;
    total_images: number;
    total_videos: number;
    images_completed: number;
    images_pending: number;
    images_failed: number;
    images_in_progress: number;
  };
  qualityDistribution: Array<{ visual_quality: number; count: number }>;
  socialDistribution: Array<{ social_media_score: number; count: number }>;
  marketingDistribution: Array<{ marketing_score: number; count: number }>;
  tagCounts: Array<{ tag_name: string; count: number }>;
  seasonDistribution: Array<{ season: string; count: number }>;
  peopleStats: Array<{ people_count: string; count: number }>;
  recentActivity: Array<{ date: string; processed_count: number }>;
  processingRate: number;
  lastUpdated: string;
}

export interface SummaryStats {
  total_images: number;
  processed_images: number;
  pending_images: number;
  avg_quality: number;
  avg_social_score: number;
  avg_marketing_score: number;
  unique_tags_used: number;
  images_with_people: number;
  completion_percentage: number;
}