const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const path = require('path');
require('dotenv').config();

const imageRoutes = require('./routes/images');
const searchRoutes = require('./routes/search');
const statsRoutes = require('./routes/stats');
const thumbnailRoutes = require('./routes/thumbnails');
const downloadRoutes = require('./routes/download');
const databaseRoutes = require('./routes/databases');
const { createPlaceholder } = require('./utils/placeholder');

const app = express();
const PORT = process.env.PORT || 5005;

// Configure trust proxy for rate limiting
// In development, we might be behind a proxy (like webpack-dev-server)
app.set('trust proxy', process.env.NODE_ENV === 'production' ? 1 : false);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https:"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:", "blob:"],
      connectSrc: ["'self'", "https:"],
    },
  },
}));

// Middleware (must come before auth middleware)
app.use(compression());
app.use(morgan('combined'));
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? process.env.FRONTEND_URL 
    : ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:3005', 'http://127.0.0.1:3005'],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Rate limiting (with better trust proxy handling)
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: process.env.NODE_ENV === 'development' ? 10000 : 1000, // Higher limit in dev
  message: 'Too many requests from this IP, please try again later.',
  skip: (req) => req.path === '/api/login', // Skip rate limiting for login
  trustProxy: process.env.NODE_ENV === 'production' ? 1 : false // Match main trust proxy setting
});
app.use('/api/', limiter);

// Login endpoint (must come before auth middleware)
app.post('/api/login', (req, res) => {
  const { password } = req.body;
  
  if (password === 'LV81868LV') {
    res.json({ success: true });
  } else {
    res.status(401).json({ error: 'Invalid password' });
  }
});

// Lightweight placeholder image endpoint (before auth middleware)
app.get('/api/placeholder-image', async (req, res) => {
  try {
    const size = req.query.size || '400x300';
    const [width, height] = size.split('x').map(Number);
    const image = await createPlaceholder(width, height);
    res.set('Content-Type', 'image/png');
    res.send(image);
  } catch (e) {
    res.status(500).end();
  }
});

// Simple password protection middleware (after body parser and login endpoint)
app.use('/api', (req, res, next) => {
  // Skip auth for health check and login endpoint
  if (req.path === '/health' || req.path === '/login' || req.path === '/placeholder-image') {
    return next();
  }
  
  // Check for password in header
  const password = req.headers['x-password'];
  
  if (password !== 'LV81868LV') {
    return res.status(401).json({ error: 'Authentication required' });
  }
  
  next();
});

// API routes
app.use('/api/images', imageRoutes);
app.use('/api/search', searchRoutes);
app.use('/api/stats', statsRoutes);
app.use('/api/thumbnails', thumbnailRoutes);
app.use('/api/download', downloadRoutes);
app.use('/api/databases', databaseRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// Serve static files from React build in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  // Handle React routing - serve index.html for all non-API routes
  app.use((req, res, next) => {
    if (req.path.startsWith('/api/')) {
      return next();
    }
    res.sendFile(path.join(__dirname, '../client/build', 'index.html'));
  });
}

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err.stack);
  
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  res.status(err.status || 500).json({
    message: err.message,
    ...(isDevelopment && { stack: err.stack })
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ message: 'Route not found' });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received. Shutting down gracefully...');
  process.exit(0);
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`Database: ${process.env.DATABASE_PATH || '../image_metadata.db'}`);
});

module.exports = app;