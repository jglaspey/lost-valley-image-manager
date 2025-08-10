#!/bin/bash
# Initial server setup script for Ubuntu on Digital Ocean
# Run this after creating your droplet

set -e  # Exit on error

echo "🚀 Lost Valley Image Manager - Server Setup Script"
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Setup firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5005/tcp  # For direct app access during testing
ufw reload

# Setup fail2ban for SSH protection
echo "🛡️ Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /var/www/lost-valley/{data,thumbnails,nginx/ssl,nginx/sites-enabled}
cd /var/www/lost-valley

# Create swap file if system has less than 2GB RAM
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
if [ $TOTAL_MEM -lt 2048 ]; then
    echo "💾 Creating 2GB swap file (system has ${TOTAL_MEM}MB RAM)..."
    if [ ! -f /swapfile ]; then
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    fi
fi

# Setup automatic security updates
echo "🔒 Configuring automatic security updates..."
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create systemd service for auto-restart
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/lost-valley.service << 'EOF'
[Unit]
Description=Lost Valley Image Manager
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/lost-valley
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lost-valley

# Setup log rotation
echo "📝 Configuring log rotation..."
cat > /etc/logrotate.d/lost-valley << 'EOF'
/var/www/lost-valley/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose -f /var/www/lost-valley/docker-compose.yml kill -s USR1 nginx
    endscript
}
EOF

echo "✅ Server setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy your application files to /var/www/lost-valley/"
echo "2. Copy your Google Drive credentials (credentials.json and token.json)"
echo "3. Copy your SQLite database to /var/www/lost-valley/data/"
echo "4. Update .env.production with your configuration"
echo "5. Run 'docker-compose up -d' to start the application"
echo ""
echo "Server Information:"
echo "- Docker version: $(docker --version)"
echo "- Docker Compose version: $(docker-compose --version)"
echo "- Application directory: /var/www/lost-valley"
echo "- Firewall: Enabled (ports 22, 80, 443, 5005 open)"
echo "- Fail2ban: Active for SSH protection"