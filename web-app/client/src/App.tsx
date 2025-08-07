import React, { useState, useMemo } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { SearchHeader } from './components/SearchHeader';
import { FilterPanel } from './components/FilterPanel';
import { ImageCard } from './components/ImageCard';
import { MasonryGallery } from './components/CSSMasonryGallery';
import { ImageDetailModal } from './components/ImageDetailModal';
import { SearchFilters, ProcessedImage } from './types/image';
import { imageApi } from './api/client';
import { Button } from './components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const initialFilters: SearchFilters = {
  query: '',
  visualQuality: [1, 5],
  hasPeople: undefined,
  peopleCount: [],
  isIndoor: undefined,
  activityTags: [],
  season: [],
  timeOfDay: [],
  socialMediaScore: [1, 5],
  marketingScore: [1, 5],
  minWidth: undefined,
  maxWidth: undefined,
  minHeight: undefined,
  maxHeight: undefined,
  aspectRatio: 'any'
};

function ImageApp() {
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedImage, setSelectedImage] = useState<ProcessedImage | null>(null);
  const [page, setPage] = useState(1);

  // Check if we're using search or just listing
  const hasActiveFilters = useMemo(() => {
    return filters.query !== '' ||
      filters.visualQuality[0] > 1 || filters.visualQuality[1] < 5 ||
      filters.hasPeople !== undefined ||
      filters.peopleCount.length > 0 ||
      filters.isIndoor !== undefined ||
      filters.activityTags.length > 0 ||
      filters.season.length > 0 ||
      filters.timeOfDay.length > 0 ||
      filters.socialMediaScore[0] > 1 || filters.socialMediaScore[1] < 5 ||
      filters.marketingScore[0] > 1 || filters.marketingScore[1] < 5 ||
      filters.minWidth !== undefined ||
      filters.maxWidth !== undefined ||
      filters.minHeight !== undefined ||
      filters.maxHeight !== undefined ||
      filters.aspectRatio !== 'any';
  }, [filters]);

  // Query for images
  const { data, isLoading, error } = useQuery({
    queryKey: ['images', filters, page, hasActiveFilters],
    queryFn: async () => {
      if (hasActiveFilters) {
        return await imageApi.searchImages({ 
          ...filters, 
          page, 
          limit: 50, 
          sort: 'created_date', 
          order: 'DESC' 
        });
      } else {
        return await imageApi.getImages({ 
          page, 
          limit: 50, 
          sort: 'created_date', 
          order: 'DESC',
          status: 'completed'
        });
      }
    },
  });

  const images = data?.images || [];
  const totalCount = data?.pagination?.total || 0;
  const totalPages = Math.ceil(totalCount / 50);

  // Filter images client-side for better performance
  const filteredImages = useMemo(() => {
    if (isLoading) {
      return [];
    }
    
    return images.filter(image => {
      // Skip filtering if no filters active - show all images
      if (!hasActiveFilters) {
        return true;
      }
      // Text search
      if (filters.query) {
        const query = filters.query.toLowerCase();
        const searchText = `${image.primary_subject} ${image.filename} ${image.notes} ${image.activity_tags.join(' ')}`.toLowerCase();
        if (!searchText.includes(query)) return false;
      }

      // Visual quality filter
      if (image.visual_quality < filters.visualQuality[0] || image.visual_quality > filters.visualQuality[1]) {
        return false;
      }

      // People filters
      if (filters.hasPeople !== undefined && image.has_people !== filters.hasPeople) {
        return false;
      }
      if (filters.peopleCount.length > 0 && !filters.peopleCount.includes(image.people_count)) {
        return false;
      }

      // Indoor/outdoor filter
      if (filters.isIndoor !== undefined && image.is_indoor !== filters.isIndoor) {
        return false;
      }

      // Activity tags filter
      if (filters.activityTags.length > 0) {
        const hasMatchingTag = filters.activityTags.some(tag => image.activity_tags.includes(tag));
        if (!hasMatchingTag) return false;
      }

      // Season filter
      if (filters.season.length > 0 && !filters.season.includes(image.season)) {
        return false;
      }

      // Time of day filter
      if (filters.timeOfDay.length > 0 && !filters.timeOfDay.includes(image.time_of_day)) {
        return false;
      }

      // Social media score filter
      if (image.social_media_score < filters.socialMediaScore[0] || image.social_media_score > filters.socialMediaScore[1]) {
        return false;
      }

      // Marketing score filter
      if (image.marketing_score < filters.marketingScore[0] || image.marketing_score > filters.marketingScore[1]) {
        return false;
      }

      return true;
    });
  }, [images, filters, hasActiveFilters, isLoading]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.query) count++;
    if (filters.visualQuality[0] > 1 || filters.visualQuality[1] < 5) count++;
    if (filters.hasPeople !== undefined) count++;
    if (filters.peopleCount.length > 0) count++;
    if (filters.isIndoor !== undefined) count++;
    if (filters.activityTags.length > 0) count++;
    if (filters.season.length > 0) count++;
    if (filters.timeOfDay.length > 0) count++;
    if (filters.socialMediaScore[0] > 1 || filters.socialMediaScore[1] < 5) count++;
    if (filters.marketingScore[0] > 1 || filters.marketingScore[1] < 5) count++;
    return count;
  }, [filters]);

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page when filters change
  };

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl mb-2">Failed to load images</h2>
          <p className="text-muted-foreground">Please check your connection and try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="bg-black text-black p-4">
        <div className="max-w-7xl mx-auto flex items-center gap-6">
          <img 
            src="https://images.squarespace-cdn.com/content/v1/614fff66a56f9d31cf50b5a4/2ff78f2d-1c62-4c4f-9590-c5cdb664d2ce/Lost+Valley+Logo-02.png?format=1500w" 
            alt="Lost Valley Logo" 
            className="w-20 h-20 object-contain invert"
          />
          <h1 className="text-4xl font-mono tracking-wider text-white" style={{fontFamily: 'VT323, monospace'}}>
            THE LV FOTOFINDER 2000
          </h1>
        </div>
      </div>

      {/* Search Header */}
      <SearchHeader
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onToggleFilters={() => setIsFiltersOpen(!isFiltersOpen)}
        isFiltersOpen={isFiltersOpen}
        activeFilterCount={activeFilterCount}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        resultCount={filteredImages.length}
      />

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Filter Panel */}
        <FilterPanel
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isOpen={isFiltersOpen}
          onToggle={() => setIsFiltersOpen(!isFiltersOpen)}
          activeFilterCount={activeFilterCount}
        />

        {/* Results Area */}
        <div className="flex-1 p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading images...</p>
              </div>
            </div>
          ) : filteredImages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg mb-2">No images found</h3>
              <p className="text-muted-foreground max-w-md">
                Try adjusting your search query or filters to find more images in your collection.
              </p>
            </div>
          ) : viewMode === 'grid' ? (
            <MasonryGallery 
              images={filteredImages} 
              onImageClick={setSelectedImage}
            />
          ) : (
            <div className="space-y-4">
              {filteredImages.map((image) => (
                <div
                  key={image.id}
                  className="flex gap-4 p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => setSelectedImage(image)}
                >
                  <img
                    src={image.drive_download_url || image.thumbnail_path}
                    alt={image.primary_subject}
                    className="w-24 h-24 object-cover rounded"
                  />
                  <div className="flex-1 space-y-2">
                    <h3 className="font-medium">{image.filename}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {image.primary_subject}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Quality: {image.visual_quality}/5</span>
                      <span>Social: {image.social_media_score}/5</span>
                      <span>Marketing: {image.marketing_score}/5</span>
                      <span>{image.has_people ? `${image.people_count} people` : 'No people'}</span>
                      <span>{image.is_indoor ? 'Indoor' : 'Outdoor'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8 pb-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                className="flex items-center gap-1"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              
              <div className="flex items-center gap-1">
                {/* Show first page */}
                {page > 3 && (
                  <>
                    <Button
                      variant={1 === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setPage(1)}
                    >
                      1
                    </Button>
                    {page > 4 && <span className="px-2 text-muted-foreground">...</span>}
                  </>
                )}
                
                {/* Show pages around current page */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                  if (pageNum > totalPages) return null;
                  
                  return (
                    <Button
                      key={pageNum}
                      variant={pageNum === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setPage(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  );
                })}
                
                {/* Show last page */}
                {page < totalPages - 2 && (
                  <>
                    {page < totalPages - 3 && <span className="px-2 text-muted-foreground">...</span>}
                    <Button
                      variant={totalPages === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setPage(totalPages)}
                    >
                      {totalPages}
                    </Button>
                  </>
                )}
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
                className="flex items-center gap-1"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
              
              <div className="ml-4 text-sm text-muted-foreground">
                Page {page} of {totalPages} ({totalCount} total images)
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Image Detail Modal */}
      <ImageDetailModal
        image={selectedImage}
        isOpen={!!selectedImage}
        onClose={() => setSelectedImage(null)}
      />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ImageApp />
      <Toaster 
        position="bottom-right"
        toastOptions={{
          className: 'bg-background text-foreground border border-border',
        }}
      />
    </QueryClientProvider>
  );
}