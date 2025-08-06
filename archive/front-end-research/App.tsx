import { useState, useMemo } from 'react';
import { SearchHeader } from './components/SearchHeader';
import { FilterPanel } from './components/FilterPanel';
import { ImageCard } from './components/ImageCard';
import { ImageDetailModal } from './components/ImageDetailModal';
import { SearchFilters, ProcessedImage } from './types/image';
import { mockImages } from './data/mockImages';

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
  marketingScore: [1, 5]
};

export default function App() {
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedImage, setSelectedImage] = useState<ProcessedImage | null>(null);

  // Filter images based on current filters
  const filteredImages = useMemo(() => {
    return mockImages.filter(image => {
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
  }, [filters]);

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

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="bg-primary text-primary-foreground p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-medium">Google Drive Image Processor</h1>
          <p className="text-primary-foreground/80 mt-1">
            Search and manage your processed permaculture image library
          </p>
        </div>
      </div>

      {/* Search Header */}
      <SearchHeader
        filters={filters}
        onFiltersChange={setFilters}
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
          onFiltersChange={setFilters}
          isOpen={isFiltersOpen}
          onToggle={() => setIsFiltersOpen(!isFiltersOpen)}
          activeFilterCount={activeFilterCount}
        />

        {/* Results Area */}
        <div className="flex-1 p-6">
          {filteredImages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg mb-2">No images found</h3>
              <p className="text-muted-foreground max-w-md">
                Try adjusting your search query or filters to find more images in your collection.
              </p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredImages.map((image) => (
                <ImageCard
                  key={image.id}
                  image={image}
                  onClick={() => setSelectedImage(image)}
                />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredImages.map((image) => (
                <div
                  key={image.id}
                  className="flex gap-4 p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => setSelectedImage(image)}
                >
                  <img
                    src={image.thumbnail_path}
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