# Simplified production Dockerfile using pre-built React files
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies
RUN npm ci --only=production

# Copy server code
COPY server/ ./server/

# Copy pre-built React files (built locally to avoid dependency conflicts)
COPY client/build/ ./client/build/

# NOTE: credentials.json and token.json will be mounted as volumes
# They are NOT included in the image for security reasons

# Expose port
EXPOSE 5005

# Start the server
CMD ["node", "server/index.js"]