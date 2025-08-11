# Lost Valley Image Manager - Deployment Guide

## Overview
This guide covers the deployment workflow for the Lost Valley Image Manager application from local development to production on Digital Ocean.

## Environment Configuration

### Local Development
- Use `.env.local` for local development settings
- Database path: `../image_metadata.db` (relative to project root)
- API URL: `http://localhost:5005/api`

### Production
- Environment variables are managed through Docker Compose
- Database path: `/app/data/image_metadata.db` (Docker volume mount)
- Nginx reverse proxy handles routing

## Deployment Workflow

### Quick Deployment
```bash
# From the web-app directory
./deploy.sh
```

The deployment script offers several options:
1. **Full deployment** - Sync files + restart services
2. **Quick sync** - Files only (faster for small changes)
3. **Restart services only** - When only configuration changed
4. **Check deployment status** - Health check and service status
5. **View remote logs** - Debug deployment issues

### Manual Deployment Steps

1. **Commit your changes locally**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Deploy to production**
   ```bash
   ./deploy.sh
   ```

3. **Verify deployment**
   - Visit http://134.199.214.90
   - Check `/api/health` endpoint
   - Review logs if needed

## Git Workflow

### Branch Strategy
- **main**: Production-ready code
- **develop** (optional): Integration branch for features
- **feature/*****: Individual feature branches

### Development Process
1. Make changes locally
2. Test with local database and environment
3. Commit changes to Git
4. Deploy to production using `./deploy.sh`
5. Verify production deployment

## File Synchronization

### Excluded from Sync
The deployment script excludes these files/folders:
- `node_modules/`
- `.git/`
- `*.log`
- `.env.local`
- `.env.development`
- `thumbnails/`
- `data/`
- `credentials.json`
- `token.json`
- `*.db`
- `.DS_Store`

### Production-Specific Files
These files exist only on the production server:
- `credentials.json` - Google Drive API credentials
- `token.json` - OAuth tokens
- `image_metadata.db` - Production database
- SSL certificates (if using HTTPS)

## Environment Differences

### Database Schema
Both environments use the same schema, but:
- Local: SQLite file in project root
- Production: SQLite file in Docker volume

### API Configuration
- Local: Direct Node.js server on port 5005
- Production: Node.js behind Nginx reverse proxy on port 80

### File Paths
- Local: Relative paths from project directory
- Production: Absolute paths in Docker container

## Troubleshooting

### Deployment Issues
```bash
# Check service status
./deploy.sh # Choose option 4

# View logs
./deploy.sh # Choose option 5

# Manual SSH access
ssh root@134.199.214.90
cd /var/www/lost-valley
docker-compose logs
```

### Common Issues
1. **Database schema mismatch**: Ensure both environments use same schema
2. **Missing credentials**: Check that Google Drive credentials are on production server
3. **Port conflicts**: Verify no other services use port 80
4. **Docker build fails**: Check available memory (add swap if needed)

## Security Notes
- Never commit credentials to Git
- Use `.env.example` as template for environment variables
- Production credentials are managed separately on server
- SSH keys are used for secure deployment access

## Monitoring
- Health endpoint: `/api/health`
- Docker service status: `docker-compose ps`
- Application logs: `docker-compose logs`
- System resources: `htop` or `docker stats`