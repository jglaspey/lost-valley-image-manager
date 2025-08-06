const express = require('express');
const router = express.Router();
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const convert = require('heic-convert');
const { createPlaceholder } = require('../utils/placeholder');
const driveService = require('../services/googleDriveAuth');

// Configure Sharp to handle more formats
sharp.cache(false); // Disable cache for development

// Create thumbnails directory if it doesn't exist
const thumbnailsDir = path.join(__dirname, '../../thumbnails');
if (!fs.existsSync(thumbnailsDir)) {
  fs.mkdirSync(thumbnailsDir, { recursive: true });
}

// Helper function to detect HEIF/HEIC files by checking magic bytes
function isHEIF(buffer) {
  if (buffer.length < 12) return false;
  
  // Check file signature (magic bytes)
  const signature = buffer.slice(4, 12).toString('ascii');
  return signature === 'ftypheic' || signature === 'ftypheix' || 
         signature === 'ftyphevc' || signature === 'ftyphevx' ||
         signature === 'ftypmif1' || signature === 'ftypmsf1';
}

// Helper function to detect HEIF by file extension
function isHEIFByName(filename) {
  const ext = path.extname(filename).toLowerCase();
  return ['.heic', '.heif', '.heix', '.hevc', '.hevx'].includes(ext);
}

// Convert HEIF to JPEG directly (no worker thread for now)
async function convertHEIFToJPEG(inputBuffer) {
  try {
    const outputBuffer = await convert({
      buffer: inputBuffer,
      format: 'JPEG',
      quality: 0.9
    });
    return outputBuffer;
  } catch (error) {
    console.error('HEIF conversion error:', error.message);
    throw error;
  }
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
    let imageBuffer = Buffer.from(fileResult.data);
    
    // Check if the image is HEIF/HEIC by file extension or magic bytes
    if (isHEIFByName(fileResult.metadata.name) || isHEIF(imageBuffer)) {
      console.log(`🔄 Converting HEIF image ${fileId} to JPEG...`);
      
      try {
        // Check for cached converted version first
        const convertedCachePath = path.join(thumbnailsDir, `${fileId}_converted.jpg`);
        
        if (fs.existsSync(convertedCachePath)) {
          console.log(`✅ Using cached converted image for ${fileId}`);
          imageBuffer = fs.readFileSync(convertedCachePath);
        } else {
          // Convert HEIF to JPEG
          const startTime = Date.now();
          imageBuffer = await convertHEIFToJPEG(imageBuffer);
          const conversionTime = Date.now() - startTime;
          
          console.log(`✅ HEIF conversion complete in ${conversionTime}ms`);
          
          // Cache the converted image
          fs.writeFileSync(convertedCachePath, imageBuffer);
        }
      } catch (error) {
        console.error('❌ HEIF conversion failed:', error.message);
        throw new Error('Failed to convert HEIF image');
      }
    }
    
    // Create thumbnail using Sharp
    const sharpInstance = sharp(imageBuffer);
    
    // Get image metadata
    const metadata = await sharpInstance.metadata();
    console.log(`Processing ${fileId}: ${metadata.format} ${metadata.width}x${metadata.height}`);
    
    // Update database with image dimensions if we have them and they're not already set
    if (metadata.width && metadata.height) {
      try {
        const db = require('../database/connection');
        await db.connect();
        
        // Check if dimensions are already set
        const existing = await db.get('SELECT width, height FROM files WHERE drive_file_id = ?', [fileId]);
        
        if (existing && (!existing.width || !existing.height)) {
          await db.run('UPDATE files SET width = ?, height = ? WHERE drive_file_id = ?', 
            [metadata.width, metadata.height, fileId]);
          console.log(`Updated dimensions for ${fileId}: ${metadata.width}x${metadata.height}`);
        }
      } catch (dbError) {
        console.error('Failed to update dimensions in database:', dbError.message);
        // Continue processing even if DB update fails
      }
    }
    
    await sharpInstance
      .resize(width, height, { 
        fit: 'inside',
        withoutEnlargement: true
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