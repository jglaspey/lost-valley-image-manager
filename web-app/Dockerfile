# Multi-stage build for production deployment

# Stage 1: Build the React frontend
FROM node:22.17-alpine AS frontend-build

WORKDIR /app/client

# Copy package files
COPY client/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY client/ ./

# Build the React app
RUN npm run build

# Stage 2: Build the Node.js backend
FROM node:22.17-alpine AS backend-build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy server code
COPY server/ ./server/

# Copy built frontend from previous stage
COPY --from=frontend-build /app/client/build ./client/build

# NOTE: credentials.json and token.json will be mounted as volumes
# They are NOT included in the image for security reasons

# Stage 3: Final production image
FROM node:22.17-alpine

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

WORKDIR /app

# Copy built application from previous stage
COPY --from=backend-build --chown=nodejs:nodejs /app ./

# Copy SQLite database (mount as volume in production)
# VOLUME ["/app/data"]

USER nodejs

EXPOSE 5000

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the server
CMD ["node", "server/index.js"]