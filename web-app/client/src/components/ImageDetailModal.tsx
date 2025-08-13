import {
  Download,
  ExternalLink,
  Calendar,
  Camera,
  Users,
  MapPin,
  Star,
  Tag,
  RotateCcw,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetClose,
} from "./ui/sheet";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { ProcessedImage } from "../types/image";
import { AuthenticatedImage } from "./AuthenticatedImage";
import { activityTagLabels } from "../constants/activityTags";
import { useState } from "react";

interface ImageDetailModalProps {
  image: ProcessedImage | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ImageDetailModal({
  image,
  isOpen,
  onClose,
}: ImageDetailModalProps) {
  if (!image) return null;

  const [dimensions, setDimensions] = useState({ width: image.width, height: image.height });
  const [version, setVersion] = useState(0);

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getQualityText = (score: number) => {
    const levels = [
      "",
      "Poor",
      "Below Average",
      "Good",
      "Really Good",
      "Excellent",
    ];
    return levels[score] || "Unknown";
  };

  const getScoreColor = (score: number) => {
    if (score >= 4) return "text-green-600";
    if (score >= 3) return "text-yellow-600";
    return "text-red-600";
  };

  const getDriveViewUrl = (fileId: string) =>
    `https://drive.google.com/file/d/${fileId}/view`;
  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/download/${image.drive_file_id}`, {
        headers: { 'x-password': localStorage.getItem('lv-password') || '' }
      });
      if (!response.ok) throw new Error(`Download failed: ${response.status}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = image.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error', err);
    }
  };

  const handleRotate = async () => {
    try {
      const response = await fetch(`/api/images/${image.id}/rotate`, {
        method: "POST",
        headers: { 'x-password': localStorage.getItem('lv-password') || '' }
      });
      if (!response.ok) throw new Error(`Rotate failed: ${response.status}`);
      setVersion(v => v + 1);
      setDimensions(({ width, height }) => ({ width: height, height: width }));
    } catch (err) {
      console.error('Rotate error', err);
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent
        side="right"
        className="p-0 !w-[1200px] !max-w-[95vw]"
        style={{ width: "1200px", maxWidth: "95vw" }}
      >
        {/* Header */}
        <SheetHeader className="p-4 pb-2 border-b">
          <div className="flex items-start justify-between">
            <SheetTitle className="text-lg pr-8 line-clamp-2">
              {image.filename}
            </SheetTitle>
            <SheetClose />
          </div>
        </SheetHeader>

        {/* Content */}
        <div className="h-[calc(100vh-80px)] overflow-y-auto">
          <div className="flex h-full">
            {/* Large Image */}
            <div className="flex-1 p-4 flex items-center justify-center relative">
              <AuthenticatedImage
                src={(image.thumbnail_path || `/api/thumbnails/${image.drive_file_id}?size=1200x900`) + `?v=${version}`}
                alt={image.primary_subject}
                className="max-w-full max-h-full object-contain bg-muted/30 rounded-lg"
                onError={() => {}}
              />
              <Button
                variant="secondary"
                size="icon"
                className="absolute bottom-4 left-4 bg-white/80"
                onClick={handleRotate}
              >
                <RotateCcw className="w-4 h-4" />
              </Button>
            </div>

            {/* Compact Metadata Sidebar */}
            <div className="w-80 p-4 border-l bg-gray-50/50 overflow-y-auto">
              {/* File Info */}
              <div className="space-y-2 mb-4">
                <div className="text-sm font-medium truncate" title={image.filename}>
                  {image.filename}
                </div>
                <div className="text-xs text-muted-foreground truncate" title={image.file_path}>
                  {image.file_path}
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatFileSize(image.file_size)} • {formatDate(image.created_date)}
                </div>
                {(dimensions.width && dimensions.height) && (
                  <div className="text-xs text-muted-foreground">
                    {dimensions.width} × {dimensions.height} pixels
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mb-4">
                <Button size="sm" className="flex-1" onClick={handleDownload}>
                  <Download className="w-3 h-3 mr-1" />
                  Download
                </Button>
                <Button variant="outline" size="sm" className="flex-1" asChild>
                  <a
                    href={getDriveViewUrl(image.drive_file_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    Drive
                  </a>
                </Button>
              </div>

              <Separator className="mb-4" />

              {/* Scores */}
              <div className="space-y-2 mb-4">
                <div className="text-xs font-medium mb-2">Quality Scores</div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center">
                    <div className={`font-medium ${getScoreColor(image.visual_quality)}`}>
                      {image.visual_quality}/5
                    </div>
                    <div className="text-muted-foreground">Visual</div>
                  </div>
                  <div className="text-center">
                    <div className={`font-medium ${getScoreColor(image.social_media_score)}`}>
                      {image.social_media_score}/5
                    </div>
                    <div className="text-muted-foreground">Social</div>
                  </div>
                  <div className="text-center">
                    <div className={`font-medium ${getScoreColor(image.marketing_score)}`}>
                      {image.marketing_score}/5
                    </div>
                    <div className="text-muted-foreground">Marketing</div>
                  </div>
                </div>
              </div>

              <Separator className="mb-4" />

              {/* Description */}
              <div className="mb-4">
                <div className="text-xs font-medium mb-2">Description</div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {image.primary_subject}
                </p>
              </div>

              {/* Quick Details */}
              <div className="space-y-2 mb-4">
                <div className="text-xs font-medium mb-2">Details</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">People:</span>
                    <span>{image.has_people ? image.people_count : 'None'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Setting:</span>
                    <span>{image.is_indoor ? 'Indoor' : 'Outdoor'}</span>
                  </div>
                  {image.season !== 'unclear' && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Season:</span>
                      <span className="capitalize">{image.season}</span>
                    </div>
                  )}
                  {image.time_of_day !== 'unclear' && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Time:</span>
                      <span className="capitalize">{image.time_of_day}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Activity Tags */}
              {image.activity_tags.length > 0 && (
                <div className="mb-4">
                  <div className="text-xs font-medium mb-2">Activity Tags</div>
                  <div className="flex flex-wrap gap-1">
                    {image.activity_tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs py-0 px-2">
                        {activityTagLabels[tag]}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Marketing Details */}
              {(image.marketing_use || image.social_media_reason) && (
                <div className="space-y-2">
                  <div className="text-xs font-medium mb-2">Usage Notes</div>
                  {image.marketing_use && (
                    <div>
                      <div className="text-xs text-muted-foreground">Marketing:</div>
                      <div className="text-xs">{image.marketing_use}</div>
                    </div>
                  )}
                  {image.social_media_reason && (
                    <div>
                      <div className="text-xs text-muted-foreground">Social Media:</div>
                      <div className="text-xs">{image.social_media_reason}</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}