const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const dbConnection = require('../database/connection');
const router = express.Router();

// Get list of available database files
router.get('/list', async (req, res) => {
  try {
    // Look for .db files in the databases directory
    const databasesDir = path.join(__dirname, '..', '..', '..');
    const files = await fs.readdir(databasesDir);
    
    // Filter for .db files
    const databases = files
      .filter(file => file.endsWith('.db'))
      .map(file => ({
        name: file,
        displayName: file.replace('.db', '').replace(/_/g, ' ').replace(/-/g, ' ')
          .split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' '),
        path: file
      }));
    
    // Sort with primary database first
    databases.sort((a, b) => {
      if (a.name === 'image_metadata.db') return -1;
      if (b.name === 'image_metadata.db') return 1;
      return a.name.localeCompare(b.name);
    });
    
    res.json({ databases });
  } catch (error) {
    console.error('Error listing databases:', error);
    res.status(500).json({ error: 'Failed to list databases' });
  }
});

// Get current database
router.get('/current', (req, res) => {
  const currentDb = process.env.DATABASE_PATH || '../image_metadata.db';
  res.json({ 
    database: currentDb,
    displayName: currentDb.replace('.db', '').replace(/_/g, ' ').replace(/-/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  });
});

// Switch database
router.post('/switch', async (req, res) => {
  try {
    const { database } = req.body;
    
    if (!database || !database.endsWith('.db')) {
      return res.status(400).json({ error: 'Invalid database name' });
    }

    // Check if database file exists
    const databasesDir = path.join(__dirname, '..', '..', '..');
    const dbPath = path.join(databasesDir, database);
    
    try {
      await fs.access(dbPath);
    } catch (error) {
      return res.status(404).json({ error: 'Database file not found' });
    }

    // Switch the database connection
    await dbConnection.setDatabase(database);
    
    // Test the connection
    await dbConnection.connect();
    
    res.json({ 
      success: true, 
      database,
      message: `Switched to database: ${database}`
    });
  } catch (error) {
    console.error('Error switching database:', error);
    res.status(500).json({ error: 'Failed to switch database' });
  }
});

module.exports = router;