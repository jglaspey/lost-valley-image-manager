# Google Drive Credentials Setup

## Important Security Note
The `credentials.json` and `token.json` files contain sensitive OAuth credentials for Google Drive access. These files are:
- **NEVER committed to Git** (they're in .gitignore)
- **NOT included in Docker images**
- **Mounted as volumes** in production

## How to Set Up Credentials

### 1. For Local Development
Place your actual `credentials.json` and `token.json` files in:
- `/web-app/credentials.json`
- `/web-app/token.json`

### 2. For Production Deployment

During deployment, you'll need to:

1. **Copy credentials to the server manually**:
```bash
# From your local machine
scp web-app/credentials.json root@YOUR_SERVER:/var/www/lost-valley/
scp web-app/token.json root@YOUR_SERVER:/var/www/lost-valley/
```

2. **Set proper permissions on the server**:
```bash
chmod 600 /var/www/lost-valley/credentials.json
chmod 600 /var/www/lost-valley/token.json
```

3. **Docker Compose will mount them** (already configured in docker-compose.production.yml):
```yaml
volumes:
  - ./credentials.json:/app/credentials.json:ro
  - ./token.json:/app/token.json
```

## Getting Google Drive Credentials

If you don't have these files yet:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Download as `credentials.json`
6. Run the authentication flow to get `token.json`

## Example Files
See `credentials.json.example` and `token.json.example` for the structure of these files.

## Security Best Practices
- Never share these files
- Rotate credentials regularly
- Use read-only permissions where possible
- Monitor API usage in Google Cloud Console