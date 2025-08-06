import {
  Download,
  ExternalLink,
  Calendar,
  Camera,
  Users,
  MapPin,
  Star,
  Tag,
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
import { activityTagLabels } from "../data/mockImages";

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
  const getDriveDownloadUrl = (fileId: string) =>
    `https://drive.google.com/uc?id=${fileId}`;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent
        side="right"
        className="p-0 !w-[1000px] !max-w-[95vw]"
        style={{ width: "1000px", maxWidth: "95vw" }}
      >
        {/* Header */}
        <SheetHeader className="p-6 pb-4 border-b">
          <div className="flex items-start justify-between">
            <SheetTitle className="text-xl pr-8 line-clamp-2">
              {image.filename}
            </SheetTitle>
            <SheetClose />
          </div>
        </SheetHeader>

        {/* Scrollable Content */}
        <div className="h-[calc(100vh-120px)] overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Image */}
            <div className="w-full">
              <img
                src={image.thumbnail_path}
                alt={image.primary_subject}
                className="w-full h-auto max-h-80 object-contain bg-muted/30 rounded-lg"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button className="flex-1" asChild>
                <a
                  href={getDriveDownloadUrl(
                    image.drive_file_id,
                  )}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download File
                </a>
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                asChild
              >
                <a
                  href={getDriveViewUrl(image.drive_file_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View in Drive
                </a>
              </Button>
            </div>

            {/* Description */}
            <div>
              <h4 className="mb-3">Description</h4>
              <p className="text-sm text-muted-foreground leading-relaxed bg-muted/30 p-4 rounded-lg">
                {image.primary_subject}
              </p>
            </div>

            <Separator />

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="flex items-center justify-center gap-1 mb-2">
                  <Star className="w-5 h-5" />
                  <span
                    className={`text-lg font-medium ${getScoreColor(image.visual_quality)}`}
                  >
                    {image.visual_quality}/5
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Visual Quality
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  ({getQualityText(image.visual_quality)})
                </div>
              </div>
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="flex items-center justify-center gap-1 mb-2">
                  <span
                    className={`text-lg font-medium ${getScoreColor(image.social_media_score)}`}
                  >
                    {image.social_media_score}/5
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Social Media
                </div>
              </div>
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="flex items-center justify-center gap-1 mb-2">
                  <span
                    className={`text-lg font-medium ${getScoreColor(image.marketing_score)}`}
                  >
                    {image.marketing_score}/5
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Marketing
                </div>
              </div>
            </div>

            <Separator />

            {/* Two-column layout for metadata */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Column */}
              <div className="space-y-6">
                {/* File Information */}
                <div className="space-y-3">
                  <h4>File Information</h4>
                  <div className="space-y-3 text-sm bg-muted/30 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        File Size:
                      </span>
                      <span>
                        {formatFileSize(image.file_size)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        Type:
                      </span>
                      <span>{image.mime_type}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        Created:
                      </span>
                      <span>
                        {formatDate(image.created_date)}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground pt-2 border-t">
                      <strong>Path:</strong> {image.file_path}
                    </div>
                  </div>
                </div>

                {/* People & Setting */}
                <div className="space-y-3">
                  <h4>People & Setting</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Users className="w-4 h-4" />
                        <span>People</span>
                      </div>
                      <span>
                        {image.has_people
                          ? image.people_count
                          : "None"}
                      </span>
                    </div>
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <MapPin className="w-4 h-4" />
                        <span>Setting</span>
                      </div>
                      <span>
                        {image.is_indoor ? "Indoor" : "Outdoor"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Activity Tags */}
                <div className="space-y-3">
                  <h4>Activities</h4>
                  <div className="flex flex-wrap gap-2">
                    {image.activity_tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {activityTagLabels[tag]}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                {/* Context */}
                <div className="space-y-3">
                  <h4>Context</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <span className="text-muted-foreground block mb-1">
                        Season
                      </span>
                      <Badge
                        variant="outline"
                        className="capitalize"
                      >
                        {image.season}
                      </Badge>
                    </div>
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <span className="text-muted-foreground block mb-1">
                        Time of Day
                      </span>
                      <Badge
                        variant="outline"
                        className="capitalize"
                      >
                        {image.time_of_day}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <span className="text-sm text-muted-foreground block mb-2">
                        Mood & Energy
                      </span>
                      <p className="text-sm">
                        {image.mood_energy}
                      </p>
                    </div>
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <span className="text-sm text-muted-foreground block mb-2">
                        Color Palette
                      </span>
                      <p className="text-sm">
                        {image.color_palette}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Social Media Feedback */}
                <div className="space-y-3">
                  <h4>Social Media Analysis</h4>
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">
                        Score
                      </span>
                      <span
                        className={`font-medium ${getScoreColor(image.social_media_score)}`}
                      >
                        {image.social_media_score}/5
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground italic">
                      {image.social_media_reason}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* AI Notes */}
            <div className="space-y-3">
              <h4>AI Notes</h4>
              <div className="bg-muted/30 p-4 rounded-lg">
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {image.notes}
                </p>
              </div>
            </div>

            {/* Bottom padding for scroll */}
            <div className="h-4"></div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}