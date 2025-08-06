# Google Drive Image Processor - UI Design Brief

## Project Overview

**System**: Automated batch processing system for Google Drive media files using local AI vision models  
**Target Users**: Permaculture community administrators, marketing teams, content creators  
**Purpose**: Transform poorly organized collections of thousands of images into a searchable, well-categorized asset library

## Current System Status

✅ **Foundation Complete**: Core architecture, data models, and AI metadata extraction schema  
🔄 **Next Phase**: User interface for searching, filtering, and managing processed images  
🎯 **Goal**: Create intuitive UI for discovering and managing community visual assets

---

## Complete Data Schema - What We're Capturing

### **File Information** (Technical Metadata)
| Field | Type | Description |
|-------|------|-------------|
| `filename` | Text | Original filename from Google Drive |
| `file_path` | Text | Full Google Drive path/location |
| `file_size` | Integer | File size in bytes |
| `mime_type` | Text | File format (image/jpeg, image/png, etc.) |
| `created_date` | Timestamp | When file was created in Drive |
| `modified_date` | Timestamp | Last modified date in Drive |
| `processing_status` | Enum | pending/in_progress/completed/failed |
| `processed_at` | Timestamp | When AI analysis was completed |
| `thumbnail_path` | Text | Path to generated thumbnail image |
| `drive_file_id` | Text | Google Drive file ID for URL generation |

### **AI-Extracted Visual Metadata** (The Rich Content Data)

#### **Core Descriptive Fields**
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `primary_subject` | Text | 1-2 sentences | Main focus/content of image |
| `visual_quality` | Integer | 1-5 scale | Image quality rating (1=blurry/poor → 5=excellent/professional) |

#### **People & Setting**
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `has_people` | Boolean | true/false | Whether people are present |
| `people_count` | Enum | none/1-2/3-5/6-10/10+ | Approximate number of people |
| `is_indoor` | Boolean | true/false | Indoor vs outdoor setting |

#### **Activity Classification**
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `activity_tags` | Array | Multiple selection | Permaculture activities (see full list below) |

**Available Activity Tags** (12 categories):
- `gardening` - Planting, weeding, tending plants
- `harvesting` - Collecting crops, fruits, vegetables  
- `education` - Workshops, teaching, demonstrations
- `construction` - Building, infrastructure projects
- `maintenance` - Repairs, upkeep, tool maintenance
- `cooking` - Food preparation, kitchen activities
- `celebration` - Events, gatherings, festivals
- `children` - Youth activities, kids learning
- `animals` - Livestock, pets, wildlife
- `landscape` - Scenic views, property overviews
- `tools` - Equipment, machinery, implements
- `produce` - Harvested goods, food products

#### **Contextual Information**
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `season` | Enum | spring/summer/fall/winter/unclear | Seasonal context if discernible |
| `time_of_day` | Enum | morning/midday/evening/unclear | Time context if discernible |
| `mood_energy` | Text | Required | Overall feeling/energy (e.g., "peaceful and serene", "vibrant and energetic") |
| `color_palette` | Text | Required | Dominant colors and mood (e.g., "warm earth tones", "cool blues and greens") |
| `notes` | Text | Required | Insights from filename, path context, and other metadata patterns |

#### **Marketing & Social Media Suitability**
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `social_media_score` | Integer | 1-5 scale | Social media suitability (1=poor/unusable, 2=below average, 3=fine/good, 4=really good, 5=fantastic/exceptional) |
| `social_media_reason` | Text | 1 sentence | Explanation for social media rating |
| `marketing_score` | Integer | 1-5 scale | Professional/marketing use rating (1=poor/unusable, 2=below average, 3=fine/good, 4=really good, 5=fantastic/exceptional) |
| `marketing_use` | Text | Category | Best use case: website banner/newsletter/social media/print materials |

---

## UI Requirements & User Workflows

### **Primary User Tasks**

1. **Discovery & Search**
   - Browse all processed images with thumbnails
   - Search by keywords in descriptions
   - Filter by multiple criteria simultaneously
   - Save and recall search queries

2. **Content Management**
   - View detailed metadata for each image
   - Edit/update AI-generated metadata fields
   - Bulk operations (tagging, categorizing)
   - Download original files or thumbnails

3. **Marketing Asset Selection**
   - Filter by marketing/social media scores
   - Find images by specific use cases
   - Identify high-quality images for campaigns
   - Export metadata for external tools

### **Key Search & Filter Scenarios**

**Marketing Team Use Cases:**
- "5-star marketing photos with produce but no people" (exceptional hero images - very rare)
- "High quality landscape shots from summer rated 4+" (best seasonal banners in collection)
- "3+ social media score with children and gardening" (good quality engagement content)

**Content Management:**
- "Education tag with 6-10 people" (workshop documentation)
- "Celebration photos with 10+ people rated 4+" (community showcase)
- "Indoor cooking activities from fall season"

**Quality Control:**
- "Images rated 1-2 for visual quality" (candidates for deletion)
- "Failed processing status" (need manual review)
- "Missing activity tags" (need additional categorization)

### **Essential UI Components**

#### **Search & Filter Interface**
- **Text Search**: Primary subject, descriptions
- **Quality Filters**: Visual quality slider (1-5)
- **People Filters**: Has people toggle + count selector
- **Setting Filter**: Indoor/outdoor toggle
- **Activity Tags**: Multi-select checkboxes (12 categories)
- **Seasonal Filter**: Season dropdown
- **Marketing Filters**: Social media score, marketing score, use case
- **Technical Filters**: File type, size, processing status

#### **Results Display**
- **Grid View**: Thumbnail gallery with key metadata overlay
- **List View**: Detailed metadata in table format
- **Detail View**: Full-size image with complete metadata panel

#### **Metadata Management**
- **Edit Mode**: Inline editing of all AI-generated fields
- **Bulk Edit**: Update multiple images simultaneously
- **Validation**: Ensure data integrity (score ranges, enum values)
- **History**: Track changes to metadata over time
- **Notes Field Display**: Show contextual insights from filename/path analysis (e.g., "From 2024 spring workshop series", "Part of harvest celebration collection")

#### **Export & Download**
- **Individual Downloads**: Original files + thumbnails
- **Bulk Export**: Selected images with metadata
- **Metadata Export**: CSV/JSON for external tools
- **Google Drive Links**: Direct access to original files
  - View URL: `https://drive.google.com/file/d/{drive_file_id}/view`
  - Download URL: `https://drive.google.com/uc?id={drive_file_id}`

---

## Technical Considerations for UI

### **Database Schema Notes**
- **Current Schema Version**: 2 (includes notes field)
- **Supported Image Formats**: JPG, JPEG, PNG, GIF, BMP, TIFF, HEIC, HEIF
- **URL Generation**: Dynamic generation of Google Drive URLs from stored file IDs
- **Notes Field**: Combines insights from filename patterns, folder structure, dates, and contextual information

### **Performance Requirements**
- **Fast Search**: Database optimized for complex queries
- **Thumbnail Loading**: Efficient image display for large collections
- **Responsive Design**: Works on desktop and tablet devices
- **Progressive Loading**: Handle thousands of images gracefully

### **Data Integration**
- **Real-time Updates**: Reflect processing status changes
- **Metadata Sync**: Changes saved immediately to database
- **Google Drive Integration**: Maintain links to original files
- **Thumbnail Management**: Efficient storage and retrieval

### **User Experience Priorities**
1. **Speed**: Fast search and filter responses
2. **Visual**: Rich thumbnail display with metadata overlays
3. **Intuitive**: Clear categorization and filtering options
4. **Flexible**: Support various workflows and use cases
5. **Reliable**: Consistent performance with large datasets

---

## Success Metrics

**Efficiency Gains:**
- Reduce image discovery time from hours to minutes
- Enable precise filtering by content and quality
- Streamline marketing asset selection process

**Content Quality:**
- Improve asset utilization through better categorization
- Identify high-value images for marketing campaigns
- Maintain organized, searchable visual library

**User Adoption:**
- Intuitive interface requiring minimal training
- Support for both casual browsing and power-user workflows
- Integration with existing content management processes

---

## Next Steps

1. **UI Mockups**: Design search interface and results display
2. **User Flow Mapping**: Define key user journeys
3. **Component Library**: Establish design system for filters and displays
4. **Prototype Development**: Build interactive prototype for testing
5. **User Testing**: Validate workflows with community administrators

**Technical Foundation**: ✅ Complete - Ready for UI development
**Data Schema**: ✅ Comprehensive - 22+ metadata fields captured (including new notes field)
**AI Processing**: ✅ Configured - Optimized for permaculture content with stricter quality scoring
**File Format Support**: ✅ Extended - Now includes HEIC/HEIF support for iPhone photos

---

*This system transforms thousands of unorganized Google Drive images into a searchable, well-categorized asset library using AI-powered metadata extraction specifically designed for permaculture communities.*