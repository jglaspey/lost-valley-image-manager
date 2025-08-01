const express = require('express');
const router = express.Router();
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const { createPlaceholder } = require('../utils/placeholder');
const driveService = require('../services/googleDriveAuth');

// Configure Sharp to handle more formats
sharp.cache(false); // Disable cache for development

// Create thumbnails directory if it doesn't exist
const thumbnailsDir = path.join(__dirname, '../../thumbnails');
if (!fs.existsSync(thumbnailsDir)) {
  fs.mkdirSync(thumbnailsDir, { recursive: true });
}

// GET /api/thumbnails/:fileId
router.get('/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    const size = req.query.size || '400x300';
    const [width, height] = size.split('x').map(Number);
    
    const thumbnailPath = path.join(thumbnailsDir, `${fileId}_${size}.jpg`);
    
    // Check if thumbnail already exists
    if (fs.existsSync(thumbnailPath)) {
      return res.sendFile(thumbnailPath);
    }
    
    // Download image using authenticated Google Drive API
    console.log(`Downloading file ${fileId} using Google Drive API...`);
    const fileResult = await driveService.downloadFile(fileId);
    
    if (!fileResult || !fileResult.data) {
      throw new Error('Failed to download file from Google Drive');
    }
    
    console.log(`Downloaded ${fileResult.metadata.name} (${fileResult.metadata.size} bytes)`);
    const response = { data: fileResult.data };
    
    // Create thumbnail using Sharp with better format support
    const sharpInstance = sharp(response.data);
    
    // Get image metadata to handle different formats
    const metadata = await sharpInstance.metadata();
    console.log(`Processing ${fileId}: ${metadata.format} ${metadata.width}x${metadata.height}`);
    
    await sharpInstance
      .resize(width, height, { 
        fit: 'cover',
        position: 'center'
      })
      .jpeg({ 
        quality: 85,
        progressive: true
      })
      .toFile(thumbnailPath);
    
    // Serve the thumbnail
    res.sendFile(thumbnailPath);
    
  } catch (error) {
    console.error('Thumbnail generation error:', error.message);
    
    try {
      // Generate a placeholder image
      const size = req.query.size || '400x300';
      const [width, height] = size.split('x').map(Number);
      const placeholderImage = await createPlaceholder(width, height);
      
      res.set('Content-Type', 'image/png');
      res.send(placeholderImage);
    } catch (placeholderError) {
      console.error('Placeholder generation error:', placeholderError.message);
      res.status(404).json({ 
        error: 'Thumbnail not available',
        fileId: req.params.fileId 
      });
    }
  }
});

module.exports = router;