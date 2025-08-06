import React from 'react';
import { MasonryInfiniteGrid } from '@egjs/react-infinitegrid';
import { Download } from 'lucide-react';
import { Button } from './ui/button';
import { ProcessedImage } from '../types/image';

interface MasonryGalleryProps {
  images: ProcessedImage[];
  onImageClick: (image: ProcessedImage) => void;
}

export function MasonryGallery({ images, onImageClick }: MasonryGalleryProps) {
  // Simple golden ratio sizing
  const getImageSize = (image: ProcessedImage) => {
    const baseWidth = 200;
    const φ = 1.618;
    
    const maxScore = Math.max(
      image.visual_quality || 0,
      image.social_media_score || 0, 
      image.marketing_score || 0
    );
    
    if (maxScore >= 5) return Math.round(baseWidth * φ * φ); // ~524px
    if (maxScore >= 4) return Math.round(baseWidth * φ);     // ~324px
    return baseWidth; // 200px
  };

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
        gap={16}
        useResizeObserver={true}
      >
        {images.map((image) => {
          const width = getImageSize(image);
          const maxScore = Math.max(
            image.visual_quality || 0,
            image.social_media_score || 0, 
            image.marketing_score || 0
          );
          
          return (
            <div
              key={`image-${image.id}`}
              data-grid-groupkey={maxScore >= 4 ? 'hero' : 'standard'}
              className="group cursor-pointer"
              style={{ width: `${width}px` }}
              onClick={() => onImageClick(image)}
            >
              <div className="bg-white rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-all duration-300">
                <div className="relative">
                  <img
                    src={image.thumbnail_path || `/api/thumbnails/${image.drive_file_id}?size=800x600`}
                    alt={image.primary_subject || image.filename}
                    className="w-full h-auto object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      if (target.nextElementSibling) {
                        target.nextElementSibling.classList.remove('hidden');
                      }
                    }}
                  />
                  <div className="hidden w-full h-48 bg-gray-200 flex items-center justify-center">
                    <div className="text-center text-gray-500 text-sm">
                      Image unavailable
                    </div>
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => handleDownload(e, image)}
                    className="absolute top-2 right-2 h-8 w-8 p-0 bg-white/90 hover:bg-white opacity-0 group-hover:opacity-100 transition-all duration-200 rounded-full"
                    title="Download original file"
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
                
                <div className="p-3 space-y-2">
                  <div className="text-sm font-medium truncate" title={image.filename}>
                    {image.filename}
                  </div>
                  <div className="text-xs text-gray-500 truncate" title={image.file_path}>
                    {image.file_path}
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <div className="flex gap-2">
                      <span className={getScoreColor(image.visual_quality || 0)}>
                        VQ: {image.visual_quality || 0}/5
                      </span>
                      <span className={getScoreColor(image.social_media_score || 0)}>
                        SM: {image.social_media_score || 0}/5
                      </span>
                      <span className={getScoreColor(image.marketing_score || 0)}>
                        MK: {image.marketing_score || 0}/5
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </MasonryInfiniteGrid>
    </div>
  );
}