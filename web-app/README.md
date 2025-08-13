# Lost Valley Image Manager Web Application

A full-stack web application for managing and searching the Lost Valley permaculture image collection with AI-extracted metadata.

## 🚀 Features

- **Advanced Search & Filtering**: Search by content, quality scores, people, activities, seasons, and more
- **Real-time Statistics**: View processing progress and image distribution insights
- **Responsive UI**: Modern React interface with dark mode support
- **REST API**: Comprehensive API for image management
- **SQLite Integration**: Direct connection to the existing image metadata database

## 📋 Prerequisites

- Node.js v22.17+ (LTS)
- npm or yarn
- SQLite database from the image processing pipeline

## 🛠️ Technology Stack

### Frontend
- React 19.1.1
- TypeScript 5.7
- Tailwind CSS 3.4
- React Query (TanStack Query) 5.62
- React Router 7.0
- Radix UI components
- Lucide icons

### Backend
- Node.js 22.17 LTS
- Express 5.1
- SQLite3
- Helmet (security)
- CORS
- Compression

## 🏃‍♂️ Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   cd web-app
   ```

2. **Install dependencies**
   ```bash
   npm run install:all
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development servers**
   ```bash
   npm run dev
   ```

   This starts:
   - Backend API on http://localhost:5000
   - React frontend on http://localhost:3000

### Production Build

1. **Build the application**
   ```bash
   npm run build
   ```

2. **Start production server**
   ```bash
   npm start
   ```

## 🚢 Deployment

### Digital Ocean App Platform

1. **Install Digital Ocean CLI**
   ```bash
   brew install doctl  # macOS
   # or follow: https://docs.digitalocean.com/reference/doctl/how-to/install/
   ```

2. **Authenticate**
   ```bash
   doctl auth init
   ```

3. **Deploy the app**
   ```bash
   npm run deploy:do
   ```

### Docker Deployment

1. **Build Docker image**
   ```bash
   npm run docker:build
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Manual Deployment

1. **Build frontend**
   ```bash
   cd client && npm run build
   ```

2. **Copy files to server**
   ```bash
   rsync -avz --exclude 'node_modules' ./ user@server:/path/to/app
   ```

3. **Install production dependencies**
   ```bash
   npm ci --only=production
   ```

4. **Start with PM2**
   ```bash
   pm2 start server/index.js --name "lost-valley-api"
   ```

## 📁 Project Structure

```
web-app/
├── client/                 # React frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app component
│   └── package.json
├── server/                 # Express backend
│   ├── database/          # Database connection
│   ├── routes/            # API routes
│   └── index.js           # Server entry point
├── .do/                   # Digital Ocean config
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Container definition
└── package.json          # Root package file
```

## 🔧 API Endpoints

### Images
- `GET /api/images` - List images with pagination
- `GET /api/images/:id` - Get single image details
- `PUT /api/images/:id/metadata` - Update image metadata

### Search
- `POST /api/search` - Advanced search with filters
- `GET /api/search/suggestions` - Get search suggestions

### Statistics
- `GET /api/stats` - Full statistics
- `GET /api/stats/summary` - Summary statistics

### Health
- `GET /api/health` - Health check endpoint

## 🔒 Security

- Helmet.js for security headers
- Rate limiting on API endpoints
- CORS configuration
- Input validation
- SQL injection prevention

## 🐛 Troubleshooting

### Database Connection Issues
- Ensure `DATABASE_PATH` in `.env` points to your SQLite database
- Check file permissions on the database file

### Port Conflicts
- Change `PORT` in `.env` if 5000 is already in use
- Update `proxy` in `client/package.json` to match

### CORS Errors
- Set `FRONTEND_URL` in `.env` for production
- Check CORS configuration in `server/index.js`

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| NODE_ENV | Environment mode | development |
| PORT | Server port | 5000 |
| DATABASE_PATH | Path to SQLite database | ./image_metadata.db |
| FRONTEND_URL | Frontend URL for CORS | http://localhost:3000 |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Lost Valley Education Center
- UI design by the Lost Valley design team
- Built with React, Node.js, and SQLite