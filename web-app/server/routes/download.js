const express = require('express');
const router = express.Router();
const driveService = require('../services/googleDriveAuth');

// GET /api/download/:fileId
router.get('/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    
    console.log(`Download request for file: ${fileId}`);
    
    // Download image using authenticated Google Drive API
    const fileResult = await driveService.downloadFile(fileId);
    
    if (!fileResult || !fileResult.data) {
      return res.status(404).json({ 
        error: 'File not found',
        fileId: fileId 
      });
    }
    
    const { data, metadata } = fileResult;
    
    // Set appropriate headers for file download
    const filename = metadata.name;
    const mimeType = metadata.mimeType || 'application/octet-stream';
    
    res.set({
      'Content-Type': mimeType,
      'Content-Length': data.byteLength,
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Cache-Control': 'public, max-age=3600' // Cache for 1 hour
    });
    
    console.log(`Serving download: ${filename} (${data.byteLength} bytes)`);
    
    // Send the file data
    res.send(Buffer.from(data));
    
  } catch (error) {
    console.error('Download error:', error.message);
    
    res.status(500).json({ 
      error: 'Download failed',
      message: error.message,
      fileId: req.params.fileId 
    });
  }
});

module.exports = router;