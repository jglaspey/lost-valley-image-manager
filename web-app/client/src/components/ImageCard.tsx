import { Download } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { ProcessedImage } from '../types/image';

interface ImageCardProps {
  image: ProcessedImage;
  onClick: () => void;
}

export function ImageCard({ image, onClick }: ImageCardProps) {
  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card onClick from firing
    const downloadUrl = `/api/download/${image.drive_file_id}`;
    
    // Create a hidden link and trigger download
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

  return (
    <div className="group hover:shadow-lg transition-all duration-200 cursor-pointer bg-white rounded-lg border overflow-hidden" onClick={onClick}>
      <div className="relative">
        <img
          src={image.thumbnail_path || `/api/thumbnails/${image.drive_file_id}?size=300x300`}
          alt={image.primary_subject}
          className="w-full aspect-square object-contain bg-gray-50"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            target.nextElementSibling?.classList.remove('hidden');
          }}
        />
        <div className="hidden w-full aspect-square bg-gray-200 flex items-center justify-center">
          <div className="text-center text-gray-500 text-xs">
            <div>Image unavailable</div>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDownload}
          className="absolute top-1 right-1 h-6 w-6 p-0 bg-white/80 hover:bg-white opacity-0 group-hover:opacity-100 transition-opacity"
          title="Download original file"
        >
          <Download className="w-3 h-3" />
        </Button>
      </div>
      
      <div className="p-2 space-y-1">
        <div className="text-xs font-medium truncate" title={image.filename}>
          {image.filename}
        </div>
        <div className="text-xs text-gray-500 truncate" title={image.file_path}>
          {image.file_path}
        </div>
        <div className="flex justify-between items-center text-xs">
          <div className="flex gap-2">
            <span className={`${getScoreColor(image.visual_quality)}`}>
              VQ: {image.visual_quality}/5
            </span>
            <span className={`${getScoreColor(image.social_media_score)}`}>
              SM: {image.social_media_score}/5
            </span>
            <span className={`${getScoreColor(image.marketing_score)}`}>
              MK: {image.marketing_score}/5
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}