import React, { useMemo } from 'react';
import { MasonryInfiniteGrid } from '@egjs/react-infinitegrid';
import { Download } from 'lucide-react';
import { Button } from './ui/button';
import { ProcessedImage } from '../types/image';

interface MasonryGalleryProps {
  images: ProcessedImage[];
  onImageClick: (image: ProcessedImage) => void;
}

export function MasonryGallery({ images, onImageClick }: MasonryGalleryProps) {
  // Golden ratio sizing calculation
  const getImageSize = (image: ProcessedImage) => {
    const baseWidth = 200;
    const φ = 1.618; // Golden ratio
    
    // Get the highest score from all three metrics
    const maxScore = Math.max(
      image.visual_quality,
      image.social_media_score, 
      image.marketing_score
    );
    
    // 10% chance for random size bump for visual interest
    const randomBump = Math.random() < 0.1;
    
    let width = baseWidth;
    
    if (maxScore >= 5 || randomBump) {
      width = baseWidth * φ * φ; // ~524px for score 5s
    } else if (maxScore >= 4) {
      width = baseWidth * φ; // ~324px for score 4s  
    } else if (maxScore >= 3) {
      width = baseWidth; // 200px for score 3s
    } else {
      width = baseWidth / φ; // ~124px for scores 1-2
    }
    
    return Math.round(width);
  };

  // Process images with size data
  const processedImages = useMemo(() => {
    return images.map((image, index) => {
      const width = getImageSize(image);
      const maxScore = Math.max(
        image.visual_quality,
        image.social_media_score, 
        image.marketing_score
      );
      
      return {
        ...image,
        width,
        groupKey: maxScore >= 4 ? 'hero' : 'standard', // For organic clustering
        key: `image-${image.id}-${index}` // Unique key for React
      };
    });
  }, [images]);

  const handleDownload = (e: React.MouseEvent, image: ProcessedImage) => {
    e.stopPropagation();
    const downloadUrl = `/api/download/${image.drive_file_id}`;
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = image.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600 font-medium';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (images.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="text-6xl mb-4">🔍</div>
        <h3 className="text-lg mb-2">No images found</h3>
        <p className="text-muted-foreground max-w-md">
          Try adjusting your search query or filters to find more images in your collection.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <MasonryInfiniteGrid
        className="w-full"
        gap={16} // 16px spacing between items
        useResizeObserver={true}
        observeChildren={true}
        transitionDuration={300}
      >
        {processedImages.map((item) => (
          <div
            key={item.key}
            data-grid-groupkey={item.groupKey}
            data-grid-width={item.width}
            className="group cursor-pointer transition-all duration-300 hover:shadow-xl"
            style={{ width: `${item.width}px` }}
            onClick={() => onImageClick(item)}
          >
            <div className="relative bg-white rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-all duration-300">
              {/* Image */}
              <div className="relative">
                <img
                  src={item.thumbnail_path || `/api/thumbnails/${item.drive_file_id}?size=800x600`}
                  alt={item.primary_subject}
                  className="w-full h-auto object-cover"
                  style={{ aspectRatio: 'auto' }}
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    target.nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <div className="hidden w-full h-48 bg-gray-200 flex items-center justify-center">
                  <div className="text-center text-gray-500 text-sm">
                    <div>Image unavailable</div>
                  </div>
                </div>
                
                {/* Download Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => handleDownload(e, item)}
                  className="absolute top-2 right-2 h-8 w-8 p-0 bg-white/90 hover:bg-white opacity-0 group-hover:opacity-100 transition-all duration-200 rounded-full"
                  title="Download original file"
                >
                  <Download className="w-4 h-4" />
                </Button>
              </div>
              
              {/* Metadata */}
              <div className="p-3 space-y-2">
                <div className="text-sm font-medium truncate" title={item.filename}>
                  {item.filename}
                </div>
                <div className="text-xs text-gray-500 truncate" title={item.file_path}>
                  {item.file_path}
                </div>
                <div className="flex justify-between items-center text-xs">
                  <div className="flex gap-2">
                    <span className={`${getScoreColor(item.visual_quality)}`}>
                      VQ: {item.visual_quality}/5
                    </span>
                    <span className={`${getScoreColor(item.social_media_score)}`}>
                      SM: {item.social_media_score}/5
                    </span>
                    <span className={`${getScoreColor(item.marketing_score)}`}>
                      MK: {item.marketing_score}/5
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </MasonryInfiniteGrid>
    </div>
  );
}