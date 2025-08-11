#!/bin/bash
# Lost Valley Image Manager - Deployment Script
# This script handles deployment to the production server

set -e  # Exit on error

# Configuration
REMOTE_USER="root"
REMOTE_HOST="134.199.214.90"
REMOTE_PATH="/var/www/lost-valley"
LOCAL_PATH="/Users/jasonglaspey/Coding/Lost Valley - Image Management/web-app"

echo "🚀 Lost Valley Image Manager - Deployment Script"
echo "================================================="

# Function to check if we're in the correct directory
check_directory() {
    if [ ! -f "package.json" ] || [ ! -d "server" ] || [ ! -d "client" ]; then
        echo "❌ Error: Please run this script from the web-app directory"
        exit 1
    fi
}

# Function to check if there are uncommitted changes
check_git_status() {
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  Warning: You have uncommitted changes. Please commit or stash them first."
        echo "Current status:"
        git status --short
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to sync files to remote server
sync_files() {
    echo "📦 Syncing files to production server..."
    
    # Create rsync exclude list
    cat > /tmp/rsync-exclude << 'EOF'
node_modules/
.git/
*.log
.env.local
.env.development
thumbnails/
data/
credentials.json
token.json
*.db
.DS_Store
EOF
    
    rsync -avz --delete --exclude-from=/tmp/rsync-exclude \
        "$LOCAL_PATH/" \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
    
    rm /tmp/rsync-exclude
    echo "✅ Files synced successfully"
}

# Function to restart services on remote server
restart_services() {
    echo "🔄 Restarting services on production server..."
    
    ssh "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
cd /var/www/lost-valley

# Stop existing containers
docker-compose down

# Remove old images (optional - saves space)
docker image prune -f

# Start services
docker-compose up -d --build

# Show status
docker-compose ps

echo "✅ Services restarted successfully"
EOF
}

# Function to check deployment health
check_health() {
    echo "🏥 Checking deployment health..."
    
    # Wait a moment for services to start
    sleep 10
    
    # Check if the health endpoint responds
    if curl -f -s "http://${REMOTE_HOST}/api/health" > /dev/null; then
        echo "✅ Health check passed - deployment successful!"
        echo "🌐 Application available at: http://${REMOTE_HOST}"
    else
        echo "❌ Health check failed - please check the logs"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && docker-compose logs --tail=50"
        exit 1
    fi
}

# Function to show deployment menu
show_menu() {
    echo "Choose deployment option:"
    echo "1) Full deployment (sync files + restart services)"
    echo "2) Quick sync (files only)"
    echo "3) Restart services only"
    echo "4) Check deployment status"
    echo "5) View remote logs"
    echo "6) Exit"
    echo
    read -p "Enter your choice (1-6): " choice
}

# Main deployment logic
main() {
    check_directory
    
    while true; do
        show_menu
        
        case $choice in
            1)
                check_git_status
                sync_files
                restart_services
                check_health
                break
                ;;
            2)
                check_git_status
                sync_files
                echo "✅ Files synced. Run option 3 to restart services."
                ;;
            3)
                restart_services
                check_health
                break
                ;;
            4)
                echo "📊 Checking deployment status..."
                ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && docker-compose ps"
                check_health
                ;;
            5)
                echo "📋 Showing recent logs..."
                ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && docker-compose logs --tail=100"
                ;;
            6)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please try again."
                ;;
        esac
        echo
    done
}

# Run the main function
main