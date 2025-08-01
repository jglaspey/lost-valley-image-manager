const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

class GoogleDriveService {
  constructor() {
    this.auth = null;
    this.drive = null;
    this.credentialsPath = path.join(__dirname, '../../credentials.json');
    this.tokenPath = path.join(__dirname, '../../token.json');
  }

  async initialize() {
    try {
      // Load credentials
      const credentials = JSON.parse(fs.readFileSync(this.credentialsPath));
      const { client_secret, client_id, redirect_uris } = credentials.installed;
      
      // Create OAuth2 client
      this.auth = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
      
      // Load existing token
      const token = JSON.parse(fs.readFileSync(this.tokenPath));
      this.auth.setCredentials(token);
      
      // Create Drive API instance
      this.drive = google.drive({ version: 'v3', auth: this.auth });
      
      console.log('Google Drive authentication initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize Google Drive auth:', error.message);
      return false;
    }
  }

  async downloadFile(fileId) {
    try {
      if (!this.drive) {
        await this.initialize();
      }

      // Get file metadata first to check if file exists
      const fileMetadata = await this.drive.files.get({
        fileId: fileId,
        fields: 'name,mimeType,size,trashed,driveId',
        supportsAllDrives: true
      });

      // Check if file is trashed
      if (fileMetadata.data.trashed) {
        throw new Error(`File ${fileId} is in trash`);
      }

      console.log(`Downloading file: ${fileMetadata.data.name} (${fileMetadata.data.mimeType}, ${fileMetadata.data.size} bytes)`);

      // Download file content
      const response = await this.drive.files.get({
        fileId: fileId,
        alt: 'media',
        supportsAllDrives: true
      }, { responseType: 'arraybuffer' });

      return {
        data: response.data,
        metadata: fileMetadata.data
      };
    } catch (error) {
      // More specific error messages
      if (error.message.includes('File not found')) {
        console.error(`Google Drive file ${fileId} not found - may have been deleted or access revoked`);
      } else if (error.message.includes('insufficient permissions')) {
        console.error(`No permission to access Google Drive file ${fileId}`);
      } else {
        console.error(`Failed to download file ${fileId}:`, error.message);
      }
      throw error;
    }
  }

  async refreshTokenIfNeeded() {
    try {
      if (!this.auth) return false;
      
      // Check if token is expired
      const tokenInfo = await this.auth.getTokenInfo(this.auth.credentials.access_token);
      
      // If expired, refresh it
      if (!tokenInfo || Date.now() >= tokenInfo.expiry_date) {
        console.log('Refreshing Google Drive token...');
        const { credentials } = await this.auth.refreshAccessToken();
        this.auth.setCredentials(credentials);
        
        // Save updated token
        fs.writeFileSync(this.tokenPath, JSON.stringify(credentials));
        console.log('Token refreshed successfully');
      }
      
      return true;
    } catch (error) {
      console.error('Failed to refresh token:', error.message);
      return false;
    }
  }
}

// Create singleton instance
const driveService = new GoogleDriveService();

module.exports = driveService;