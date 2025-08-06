import { Calendar, Users, MapPin, Star, Camera, Tag } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ProcessedImage } from '../types/image';
import { activityTagLabels } from '../data/mockImages';

interface ImageCardProps {
  image: ProcessedImage;
  onClick: () => void;
}

export function ImageCard({ image, onClick }: ImageCardProps) {
  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getQualityColor = (score: number) => {
    if (score >= 4) return 'bg-green-100 text-green-800';
    if (score >= 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card className="group hover:shadow-lg transition-all duration-200 cursor-pointer" onClick={onClick}>
      <div className="relative">
        <img
          src={image.thumbnail_path}
          alt={image.primary_subject}
          className="w-full h-48 object-cover rounded-t-lg"
        />
        <div className="absolute top-2 left-2 flex gap-1">
          <Badge className={`text-xs ${getQualityColor(image.visual_quality)}`}>
            <Star className="w-3 h-3 mr-1" />
            {image.visual_quality}/5
          </Badge>
          {image.social_media_score >= 4 && (
            <Badge variant="secondary" className="text-xs">
              Social {image.social_media_score}/5
            </Badge>
          )}
        </div>
      </div>
      
      <CardContent className="p-4 space-y-3">
        <div>
          <h3 className="font-medium line-clamp-1">{image.filename}</h3>
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {image.primary_subject}
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {formatDate(image.created_date)}
          </div>
          <div className="flex items-center gap-1">
            <Camera className="w-3 h-3" />
            {formatFileSize(image.file_size)}
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {image.has_people && (
            <div className="flex items-center gap-1 text-muted-foreground">
              <Users className="w-3 h-3" />
              {image.people_count}
            </div>
          )}
          <div className="flex items-center gap-1 text-muted-foreground">
            <MapPin className="w-3 h-3" />
            {image.is_indoor ? 'Indoor' : 'Outdoor'}
          </div>
          {image.season !== 'unclear' && (
            <Badge variant="outline" className="text-xs capitalize">
              {image.season}
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap gap-1">
          {image.activity_tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {activityTagLabels[tag]}
            </Badge>
          ))}
          {image.activity_tags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{image.activity_tags.length - 3} more
            </Badge>
          )}
        </div>

        <div className="flex justify-between items-center pt-2 border-t">
          <div className="flex gap-2 text-xs">
            <span className={`${getScoreColor(image.social_media_score)}`}>
              SM: {image.social_media_score}/5
            </span>
            <span className={`${getScoreColor(image.marketing_score)}`}>
              MK: {image.marketing_score}/5
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}