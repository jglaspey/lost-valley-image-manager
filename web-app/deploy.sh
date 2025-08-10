#!/bin/bash
# Deployment script for Digital Ocean

echo "🚀 Starting deployment to Digital Ocean..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="root"
APP_DIR="/var/www/lost-valley"

# Check if server IP is set
if [ "$SERVER_IP" = "YOUR_SERVER_IP" ]; then
    echo -e "${RED}❌ Please update SERVER_IP in this script with your Digital Ocean droplet IP${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Building Docker image locally...${NC}"
docker build -t lost-valley-app ./

echo -e "${YELLOW}📤 Saving and compressing Docker image...${NC}"
docker save lost-valley-app | gzip > lost-valley-app.tar.gz

echo -e "${YELLOW}📡 Uploading to server...${NC}"
scp lost-valley-app.tar.gz ${SERVER_USER}@${SERVER_IP}:~/

echo -e "${YELLOW}📋 Copying configuration files...${NC}"
scp docker-compose.production.yml ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/docker-compose.yml
scp .env.production ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/.env
scp -r ../databases/*.db ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/data/

echo -e "${YELLOW}🔧 Loading image and starting services on server...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
    cd /var/www/lost-valley
    docker load < ~/lost-valley-app.tar.gz
    docker-compose down
    docker-compose up -d
    docker-compose ps
    rm ~/lost-valley-app.tar.gz
ENDSSH

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "Visit http://${SERVER_IP}:5005 to see your app"