# Lost Valley Image Manager - Deployment Guide (Railway)

We have migrated production to Railway. The DigitalOcean droplet process below is archived.

## 📋 Prerequisites
- Railway account and CLI
- GitHub repository access
- Google Drive credentials (service account recommended)

## 🚀 Railway Deployment

### Configure variables
Use one of the two auth modes.

Service account (recommended):
```bash
railway variables set GOOGLE_SERVICE_ACCOUNT_JSON="$(cat /absolute/path/to/service-account.json)"
```

OAuth client + token:
```bash
railway variables set \
  GOOGLE_OAUTH_CLIENT_JSON="$(cat /absolute/path/to/credentials.json)" \
  GOOGLE_OAUTH_TOKEN_JSON="$(cat /absolute/path/to/token.json)"
```

Optional app vars:
```bash
railway variables set LV_PASSWORD="your-password"
```

### Deploy
```bash
git add -A && git commit -m "deploy" && git push
railway up
```

### Verify
- Open the deployment URL (`*.up.railway.app`)
- Check `/api/health`
- Watch logs: `railway logs -f`

### Notes
- We force HTTPS redirect in production.
- Thumbnails and original downloads are cached on disk inside the container and persist only for the lifetime of a deployment.

---

## Archived: DigitalOcean Instructions
### Step 1: Create Digital Ocean Droplet

1. **Log into Digital Ocean** and click "Create" → "Droplets"

2. **Choose an image**: Ubuntu 22.04 LTS

3. **Choose a plan**:
   - Basic shared CPU
   - Regular SSD
   - $12/month (2GB RAM, 2 vCPUs, 60GB SSD) - Recommended minimum
   - $6/month (1GB RAM, 1 vCPU, 25GB SSD) - Will work but may be slow

4. **Choose datacenter**: Select closest to your users

5. **Authentication**: 
   - Add your SSH key (recommended)
   - Or use password (less secure)

6. **Additional options**:
   - ✅ Enable backups ($2/month - recommended)
   - ✅ Enable monitoring

7. **Finalize**:
   - Hostname: `lost-valley-app`
   - Click "Create Droplet"

8. **Note your server's IP address** (e.g., 165.232.xxx.xxx)

### Step 2: Initial Server Setup

1. **SSH into your server**:
```bash
ssh root@YOUR_SERVER_IP
```

2. **Download and run the setup script**:
```bash
# Download the setup script
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/web-app/server-setup.sh

# Make it executable
chmod +x server-setup.sh

# Run it
./server-setup.sh
```

This script will:
- Update system packages
- Install Docker and Docker Compose
- Configure firewall
- Setup fail2ban for security
- Create application directories
- Configure automatic updates

### Step 3: Transfer Application Files

**On your local machine:**

1. **Update configuration files**:
```bash
# Edit the deployment script with your server IP
nano web-app/deploy.sh
# Change SERVER_IP="YOUR_SERVER_IP" to your actual IP

# Edit production environment
nano web-app/.env.production
# Update FRONTEND_URL with your domain (or http://YOUR_SERVER_IP:5005)
```

2. **Create a deployment package**:
```bash
cd "Lost Valley - Image Management/web-app"

# Create a tar archive with all necessary files
tar -czf deployment.tar.gz \
  Dockerfile \
  docker-compose.production.yml \
  .env.production \
  package*.json \
  server/ \
  client/build/ \
  credentials.json \
  token.json \
  nginx/

# Copy to server
scp deployment.tar.gz root@YOUR_SERVER_IP:/var/www/lost-valley/

# Copy database
scp ../databases/image_metadata.db root@YOUR_SERVER_IP:/var/www/lost-valley/data/
```

### Step 4: Deploy on Server

**On the server:**

1. **Extract and setup files**:
```bash
cd /var/www/lost-valley
tar -xzf deployment.tar.gz
rm deployment.tar.gz

# Rename production compose file
mv docker-compose.production.yml docker-compose.yml

# Set proper permissions
chmod 600 credentials.json token.json
chmod 644 .env.production
```

2. **Build and start the application**:
```bash
# Build the Docker image
docker build -t lost-valley-app .

# Start the services
docker-compose up -d

# Check if everything is running
docker-compose ps

# View logs
docker-compose logs -f
```

3. **Test the application**:
```bash
# Test health endpoint
curl http://localhost:5005/api/health

# Should return something like:
# {"status":"healthy","timestamp":"2024-...","uptime":10.5,"environment":"production"}
```

### Step 5: Configure Domain and SSL (Optional but Recommended)

1. **Point your domain to the server**:
   - Go to your domain registrar
   - Add an A record: `@` → `YOUR_SERVER_IP`
   - Add an A record: `www` → `YOUR_SERVER_IP`
   - Wait for DNS propagation (5-30 minutes)

2. **Install Certbot for free SSL certificates**:
```bash
# On the server
apt-get install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker-compose stop nginx

# Get SSL certificate
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Certificates will be in:
# /etc/letsencrypt/live/your-domain.com/
```

3. **Update Nginx configuration**:
```bash
# Edit the nginx config
nano /var/www/lost-valley/nginx/sites-enabled/lost-valley.conf

# Update server_name from _ to your-domain.com
# Uncomment the HTTPS server block
# Update paths to SSL certificates
```

4. **Copy SSL certificates to Docker volume**:
```bash
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /var/www/lost-valley/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /var/www/lost-valley/nginx/ssl/key.pem
chmod 644 /var/www/lost-valley/nginx/ssl/cert.pem
chmod 600 /var/www/lost-valley/nginx/ssl/key.pem
```

5. **Restart services**:
```bash
docker-compose restart
```

6. **Setup auto-renewal**:
```bash
# Add to crontab
crontab -e

# Add this line:
0 2 * * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /var/www/lost-valley/nginx/ssl/cert.pem && cp /etc/letsencrypt/live/your-domain.com/privkey.pem /var/www/lost-valley/nginx/ssl/key.pem && docker-compose -f /var/www/lost-valley/docker-compose.yml restart nginx
```

### Step 6: Monitoring and Maintenance

1. **View application logs**:
```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs -f app
```

2. **Monitor system resources**:
```bash
# Check Docker containers
docker ps
docker stats

# System resources
htop

# Disk usage
df -h
```

3. **Backup your data**:
```bash
# Create backup script
cat > /root/backup-lost-valley.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/lost-valley"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /var/www/lost-valley/data/image_metadata.db $BACKUP_DIR/image_metadata_$DATE.db

# Backup credentials
tar -czf $BACKUP_DIR/credentials_$DATE.tar.gz \
  /var/www/lost-valley/credentials.json \
  /var/www/lost-valley/token.json

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup-lost-valley.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 3 * * * /root/backup-lost-valley.sh") | crontab -
```

4. **Update the application**:
```bash
# Pull latest changes
cd /var/www/lost-valley
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## 🎉 Success Checklist

- [ ] Droplet created and accessible via SSH
- [ ] Docker and Docker Compose installed
- [ ] Application files transferred
- [ ] Database copied
- [ ] Google Drive credentials in place
- [ ] Application running (check http://YOUR_SERVER_IP:5005)
- [ ] Domain configured (optional)
- [ ] SSL certificates installed (optional)
- [ ] Backups configured
- [ ] Monitoring enabled

## 🚨 Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs app

# Check if ports are in use
netstat -tulpn | grep -E '5005|80|443'

# Restart everything
docker-compose down
docker-compose up -d
```

### Database issues
```bash
# Check database file exists
ls -la /var/www/lost-valley/data/

# Check permissions
chown -R 1001:1001 /var/www/lost-valley/data/
```

### Google Drive authentication fails
```bash
# Check credentials files exist
ls -la /var/www/lost-valley/*.json

# Check file permissions
chmod 600 /var/www/lost-valley/credentials.json
chmod 600 /var/www/lost-valley/token.json
```

### Out of memory
```bash
# Check memory usage
free -h

# Add swap if needed
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify all files are in place
3. Ensure firewall rules are correct: `ufw status`
4. Check Digital Ocean's monitoring graphs for resource usage

## 🔐 Security Recommendations

1. **Use SSH keys** instead of passwords
2. **Enable automatic security updates**
3. **Regular backups** to Digital Ocean Spaces or another location
4. **Monitor logs** for suspicious activity
5. **Keep Docker images updated**
6. **Use strong passwords** in .env.production
7. **Enable rate limiting** in Nginx configuration
8. **Consider using Cloudflare** for DDoS protection

## 💰 Cost Estimation

- Droplet (2GB RAM): $12/month
- Backups: $2/month
- Domain: ~$12/year
- SSL: Free (Let's Encrypt)
- **Total: ~$14/month**

## 🎯 Next Steps

Once deployed:
1. Test all functionality thoroughly
2. Set up monitoring alerts in Digital Ocean
3. Configure external backups
4. Document your specific configuration
5. Share the URL with your team!