import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { Button } from './ui/button';
import { ProcessedImage } from '../types/image';
import { AuthenticatedImage } from './AuthenticatedImage';

interface MasonryGalleryProps {
  images: ProcessedImage[];
  onImageClick: (image: ProcessedImage) => void;
}

export function MasonryGallery({ images, onImageClick }: MasonryGalleryProps) {
  // Golden ratio sizing
  const getImageSize = (image: ProcessedImage) => {
    const baseWidth = 200;
    const φ = 1.618;
    
    const maxScore = Math.max(
      image.visual_quality || 0,
      image.social_media_score || 0, 
      image.marketing_score || 0
    );
    
    // Add some randomness (10% chance to bump up)
    const randomBump = Math.random() < 0.1;
    
    if (maxScore >= 5 || randomBump) return Math.round(baseWidth * φ * φ); // ~524px
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
    <div 
      className="w-full"
      style={{
        columnCount: 'auto',
        columnWidth: '250px',
        columnGap: '16px',
      }}
    >
      {images.map((image) => {
        const width = getImageSize(image);
        
        return (
          <ImageCard
            key={`image-${image.id}`}
            image={image}
            width={width}
            onImageClick={onImageClick}
          />
        );
      })}
    </div>
  );
}

// Separate ImageCard component with loading state
function ImageCard({ 
  image, 
  width, 
  onImageClick 
}: { 
  image: ProcessedImage; 
  width: number; 
  onImageClick: (image: ProcessedImage) => void; 
}) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const downloadUrl = `/api/download/${image.drive_file_id}`;
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = image.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      className="group cursor-pointer mb-4 inline-block w-full"
      onClick={() => onImageClick(image)}
      style={{
        breakInside: 'avoid',
        width: `${width}px`,
        maxWidth: '100%'
      }}
    >
      <div className="bg-white rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 relative">
        <div className="relative">
          {/* Loading skeleton */}
          {isLoading && (
            <div 
              className="w-full bg-gray-200 animate-pulse flex items-center justify-center"
              style={{ aspectRatio: '4/3', minHeight: '150px' }}
            >
              <div className="text-gray-400">
                <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          )}
          
          {/* Actual image */}
          <AuthenticatedImage
            src={image.thumbnail_path || `/api/thumbnails/${image.drive_file_id}?size=800x600`}
            alt={image.primary_subject || image.filename}
            className="w-full h-auto object-cover block"
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setIsLoading(false);
              setHasError(true);
            }}
          />
          
          {/* Error state */}
          {hasError && (
            <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
              <div className="text-center text-gray-500 text-sm">
                Image unavailable
              </div>
            </div>
          )}
          
          {/* Download button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            className="absolute top-2 right-2 h-8 w-8 p-0 bg-white/90 hover:bg-white opacity-0 group-hover:opacity-100 transition-all duration-200 rounded-full"
            title="Download original file"
          >
            <Download className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Simple scores on hover only - positioned on the image */}
        <div className="absolute bottom-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
          <div className="bg-black/80 text-white text-xs px-2 py-1 rounded-md">
            Q:{image.visual_quality || 0} | S:{image.social_media_score || 0} | M:{image.marketing_score || 0}
          </div>
        </div>
      </div>
    </div>
  );
}