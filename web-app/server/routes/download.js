const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');
const driveService = require('../services/googleDriveAuth');

// Ensure downloads cache directory exists
const downloadsDir = path.join(__dirname, '../../downloads');
if (!fs.existsSync(downloadsDir)) {
  fs.mkdirSync(downloadsDir, { recursive: true });
}

// GET /api/download/:fileId
router.get('/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    console.log(`Download request for file: ${fileId}`);

    // Check server-side cache first
    const cachedPath = path.join(downloadsDir, `${fileId}`);
    if (fs.existsSync(cachedPath)) {
      const stat = fs.statSync(cachedPath);
      res.set({
        'Content-Type': 'application/octet-stream',
        'Content-Length': stat.size,
        'Content-Disposition': `attachment; filename="${fileId}"`,
        'Cache-Control': 'public, max-age=3600'
      });
      return fs.createReadStream(cachedPath).pipe(res);
    }

    // Download image using authenticated Google Drive API
    const fileResult = await driveService.downloadFile(fileId);
    
    if (!fileResult || !fileResult.data) {
      return res.status(404).json({ 
        error: 'File not found',
        fileId: fileId 
      });
    }
    
    const { data, metadata } = fileResult;

    // Save to server cache for future direct serving
    const buffer = Buffer.from(data);
    try {
      fs.writeFileSync(cachedPath, buffer);
    } catch (e) {
      console.warn('Could not cache downloaded file:', e.message);
    }

    // Set appropriate headers for file download
    const filename = metadata.name;
    const mimeType = metadata.mimeType || 'application/octet-stream';
    res.set({
      'Content-Type': mimeType,
      'Content-Length': buffer.byteLength,
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Cache-Control': 'public, max-age=3600'
    });
    console.log(`Serving download: ${filename} (${buffer.byteLength} bytes)`);
    res.send(buffer);
    
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