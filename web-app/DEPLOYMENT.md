# Lost Valley Image Manager - Railway Deployment Guide

This app now deploys on Railway. It’s faster, cheaper, and simpler than our previous DigitalOcean/Docker setup. The old droplet workflow is archived below for reference.

## Quick Start

Prereqs:
- Railway CLI installed and logged in (`npm i -g @railway/cli && railway login`).
- GitHub repo connected to Railway project (already configured).

Deploy:
```bash
# From repo root
git add -A && git commit -m "deploy" && git push
railway up
```

Railway uses Nixpacks and our `railway.toml` to:
- Build client (`cd web-app && npm install && npm run build`)
- Start server (`cd web-app && npm start`)

## Environment Variables

Authentication (pick one):
- Service account (recommended)
  - `GOOGLE_SERVICE_ACCOUNT_JSON` = contents of the service account key JSON
  - Share the Drive or files with the service account email (Viewer)
- OAuth client + token
  - `GOOGLE_OAUTH_CLIENT_JSON` = contents of `credentials.json`
  - `GOOGLE_OAUTH_TOKEN_JSON` = contents of `token.json`

App config:
- `LV_PASSWORD` (optional; falls back to current hard-coded password if unset)
- `FRONTEND_URL` (optional; for CORS; defaults work for Railway domain)

Set variables:
```bash
railway variables set GOOGLE_SERVICE_ACCOUNT_JSON="$(cat /absolute/path/to/service-account.json)"
# or
railway variables set \
  GOOGLE_OAUTH_CLIENT_JSON="$(cat /absolute/path/to/credentials.json)" \
  GOOGLE_OAUTH_TOKEN_JSON="$(cat /absolute/path/to/token.json)"
```

## Database

- The SQLite file `web-app/image_metadata.db` is checked into the repo for deployment convenience.
- Server logs print the DB path at boot; the app reads from `/app/web-app/image_metadata.db` in the container.

## Thumbnails and Downloads

- Thumbnails are generated on demand and cached in `/app/web-app/thumbnails/` (ephemeral per deployment on Railway).
- Full-size downloads stream from Google Drive and are cached at `/app/web-app/downloads/` during the container lifetime.

## HTTPS

- Railway provides HTTPS on `*.up.railway.app`. We force redirect HTTP→HTTPS in production.
- Custom domains and managed certificates can be configured in the Railway dashboard.

## Health Check

- `/api/health` returns process memory, system totals, env, and uptime.

## Logs and Redeploys

```bash
railway logs -f
railway up
```

---

## Archived: DigitalOcean (legacy)
The previous Docker Compose + Nginx deployment remains in `web-app/docker-compose.production.yml` and `web-app/DEPLOYMENT.md` history. We no longer maintain that path. See the root `DEPLOYMENT_GUIDE.md` for the original steps if needed.

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