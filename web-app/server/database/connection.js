const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class DatabaseConnection {
  constructor() {
    this.db = null;
    this.dbPath = process.env.DATABASE_PATH || path.join(__dirname, '../../../image_metadata.db');
    console.log('Database path configured:', this.dbPath);
    console.log('Database path exists:', require('fs').existsSync(this.dbPath));
    console.log('Current working directory:', process.cwd());
    console.log('__dirname:', __dirname);
    
    // List available database files
    const fs = require('fs');
    const rootDir = path.join(__dirname, '../../..');
    console.log('Root directory:', rootDir);
    try {
      const files = fs.readdirSync(rootDir).filter(f => f.endsWith('.db'));
      console.log('Available database files in root:', files);
    } catch (err) {
      console.log('Could not read root directory:', err.message);
    }
  }

  async setDatabase(dbName) {
    // Close existing connection if any
    if (this.db) {
      await this.close();
    }
    
    // Update the database path
    this.dbPath = path.join(__dirname, '../../../', dbName);
    console.log('Database switched to:', this.dbPath);
    
    // Reset the connection
    this.db = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      if (this.db) {
        return resolve(this.db);
      }

      this.db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) {
          console.error('Error opening database:', err.message);
          reject(err);
        } else {
          console.log('Connected to SQLite database at:', this.dbPath);
          resolve(this.db);
        }
      });
    });
  }

  async query(sql, params = []) {
    const db = await this.connect();
    return new Promise((resolve, reject) => {
      db.all(sql, params, (err, rows) => {
        if (err) {
          console.error('Database query error:', err.message);
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }

  async get(sql, params = []) {
    const db = await this.connect();
    return new Promise((resolve, reject) => {
      db.get(sql, params, (err, row) => {
        if (err) {
          console.error('Database get error:', err.message);
          reject(err);
        } else {
          resolve(row);
        }
      });
    });
  }

  async run(sql, params = []) {
    const db = await this.connect();
    return new Promise((resolve, reject) => {
      db.run(sql, params, function(err) {
        if (err) {
          console.error('Database run error:', err.message);
          reject(err);
        } else {
          resolve({ lastID: this.lastID, changes: this.changes });
        }
      });
    });
  }

  close() {
    return new Promise((resolve, reject) => {
      if (this.db) {
        this.db.close((err) => {
          if (err) {
            console.error('Error closing database:', err.message);
            reject(err);
          } else {
            console.log('Database connection closed.');
            this.db = null;
            resolve();
          }
        });
      } else {
        resolve();
      }
    });
  }
}

// Create a singleton instance
const dbConnection = new DatabaseConnection();

module.exports = dbConnection;