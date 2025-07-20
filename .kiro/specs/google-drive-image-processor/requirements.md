# Requirements Document

## Introduction

This feature enables automated processing and cataloging of images and videos stored across Google Drive folders for an online community. The system will traverse the entire Drive structure, identify media files, extract metadata using local LLM vision analysis, and store the results in a queryable database. The goal is to transform a poorly organized collection of thousands of media files into a searchable, well-categorized asset library for social media and marketing use.

## Requirements

### Requirement 1

**User Story:** As a community administrator, I want to automatically discover all images and videos in our Google Drive, so that no media files are missed during processing.

#### Acceptance Criteria

1. WHEN the system starts processing THEN it SHALL traverse all folders and subfolders in the specified Google Drive
2. WHEN encountering a file THEN the system SHALL identify if it is an image or video based on file extension
3. WHEN processing is complete THEN the system SHALL provide a count of total media files discovered
4. IF a folder is inaccessible due to permissions THEN the system SHALL log the error and continue processing other folders

### Requirement 2

**User Story:** As a community administrator, I want to extract detailed metadata from each image using AI analysis, so that I can later search and filter images based on their content.

#### Acceptance Criteria

1. WHEN processing an image THEN the system SHALL analyze it using a local LLM vision model
2. WHEN analyzing an image THEN the system SHALL extract metadata including: primary subject description, visual quality rating (1-5), people presence and count, activity tags from permaculture categories, social media score with reasoning, and marketing score with use case
3. WHEN analysis is complete THEN the system SHALL store the metadata in a structured format
4. IF an image cannot be processed THEN the system SHALL log the error and mark the file as failed

### Requirement 3

**User Story:** As a community administrator, I want to track which files have been processed, so that I can resume processing after interruptions and avoid duplicate work.

#### Acceptance Criteria

1. WHEN a file is discovered THEN the system SHALL record its path, filename, and processing status in a database
2. WHEN processing begins for a file THEN the system SHALL update its status to "in_progress"
3. WHEN processing completes successfully THEN the system SHALL update the status to "completed"
4. WHEN the system restarts THEN it SHALL only process files that are not marked as "completed"
5. IF processing fails for a file THEN the system SHALL mark it as "failed" and allow retry

### Requirement 4

**User Story:** As a community administrator, I want to store file location and create thumbnails, so that I can quickly identify and access the original files.

#### Acceptance Criteria

1. WHEN processing a media file THEN the system SHALL record its full Google Drive path
2. WHEN processing an image THEN the system SHALL create a small thumbnail version
3. WHEN storing results THEN the system SHALL maintain the relationship between original file location and thumbnail
4. WHEN a file is moved in Google Drive THEN the system SHALL be able to handle path changes in future versions

### Requirement 5

**User Story:** As a community member, I want to search and filter the processed images using various criteria, so that I can quickly find suitable images for specific purposes.

#### Acceptance Criteria

1. WHEN searching THEN the system SHALL support filtering by primary subject keywords
2. WHEN searching THEN the system SHALL support filtering by activity tags (gardening, harvesting, education, etc.)
3. WHEN searching THEN the system SHALL support filtering by presence and count of people
4. WHEN searching THEN the system SHALL support filtering by visual quality, social media score, and marketing score ratings
5. WHEN displaying results THEN the system SHALL show thumbnails with key metadata
6. WHEN selecting a result THEN the system SHALL provide the original file location in Google Drive

### Requirement 6

**User Story:** As a system operator, I want the processing to run in batch mode on my local machine, so that I have full control over when and how the processing occurs.

#### Acceptance Criteria

1. WHEN I trigger the process THEN it SHALL run as a batch job on my local Mac computer
2. WHEN processing THEN the system SHALL use a local LLM for image analysis
3. WHEN processing THEN the system SHALL provide progress updates and logging
4. WHEN processing completes THEN the system SHALL provide a summary report of results
5. IF I stop the process THEN it SHALL be able to resume from where it left off

### Requirement 7

**User Story:** As a community administrator, I want all processed data stored in a database, so that I can perform complex queries and maintain the data long-term.

#### Acceptance Criteria

1. WHEN storing metadata THEN the system SHALL use a structured database schema
2. WHEN storing data THEN the system SHALL ensure data integrity and consistency
3. WHEN querying THEN the system SHALL support complex filtering and sorting operations
4. WHEN the database grows large THEN the system SHALL maintain acceptable query performance
5. IF database operations fail THEN the system SHALL handle errors gracefully and provide meaningful error messages