const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

class DatabaseConnection {
  constructor() {
    this.db = null;
    // Resolve DATABASE_PATH to an absolute path. If unset, default to the
    // canonical database bundled with the app at web-app/image_metadata.db
    const resolveDbPath = (inputPath) => {
      const webAppDir = path.resolve(__dirname, '..', '..');
      const defaultPath = path.join(webAppDir, 'image_metadata.db');
      if (!inputPath) return defaultPath;

      // Absolute path: use as-is
      if (path.isAbsolute(inputPath)) return inputPath;

      // Relative path: resolve against web-app directory
      const candidate = path.resolve(webAppDir, inputPath);
      // Prevent paths that escape the web-app directory (e.g., ../image_metadata.db)
      const rel = path.relative(webAppDir, candidate);
      if (rel.startsWith('..')) {
        console.warn(`[db] Ignoring DATABASE_PATH outside web-app (${inputPath}); using default: ${defaultPath}`);
        return defaultPath;
      }
      return candidate;
    };

    // Debug logs to trace resolution context
    console.log('[db] __dirname =', __dirname);
    console.log('[db] env.DATABASE_PATH =', process.env.DATABASE_PATH || '<unset>');

    this.dbPath = resolveDbPath(process.env.DATABASE_PATH);
    const defaultPath = path.resolve(__dirname, '..', '..', 'image_metadata.db');
    if (!fs.existsSync(this.dbPath) && fs.existsSync(defaultPath)) {
      console.warn(`Database path not found at ${this.dbPath}. Falling back to default: ${defaultPath}`);
      this.dbPath = defaultPath;
    }
    console.log('Database path resolved to:', this.dbPath);
  }

  async setDatabase(dbName) {
    // Close existing connection if any
    if (this.db) {
      await this.close();
    }
    
    // Update the database path (support relative names like "image_metadata.db")
    this.dbPath = path.isAbsolute(dbName)
      ? dbName
      : path.resolve(__dirname, '..', '..', dbName);
    console.log('Database switched to:', this.dbPath);
    
    // Reset the connection
    this.db = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      if (this.db) {
        return resolve(this.db);
      }

      const tryOpen = (filePath, onFail) => {
        return new Promise((res, rej) => {
          const db = new sqlite3.Database(filePath, sqlite3.OPEN_READWRITE, (err) => {
            if (err) return rej(err);
            this.db = db;
            console.log('Connected to SQLite database at:', filePath);
            this.db.all("SELECT name FROM sqlite_master WHERE type='table'", (tblErr, tables) => {
              if (tblErr) {
                console.error('Error checking tables:', tblErr.message);
              } else {
                console.log('Available tables:', (tables || []).map(t => t.name).join(', '));
              }
            });
            res(db);
          });
        }).catch(async (e) => {
          if (onFail) return onFail(e);
          throw e;
        });
      };

      tryOpen(this.dbPath, async (err) => {
        // If initial open fails (e.g., file missing), try default path if present
        const fallback = path.resolve(__dirname, '..', '..', 'image_metadata.db');
        if (this.dbPath !== fallback && fs.existsSync(fallback)) {
          console.warn(`Failed to open DB at ${this.dbPath} (${err.message}). Falling back to ${fallback}`);
          this.dbPath = fallback;
          return tryOpen(this.dbPath);
        }
        console.error('Error opening database:', err.message);
        throw err;
      }).then(resolve).catch(reject);
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