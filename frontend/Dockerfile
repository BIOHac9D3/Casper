# Casper Frontend - Multi-Stage Dockerfile
# Stage 1: Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files first for better caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy all frontend files
COPY frontend/ .

# Build the application
RUN npm run build

# Stage 2: Runtime stage
FROM node:18-alpine

WORKDIR /app

# Copy built files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

# Create non-root user for security
RUN adduser -D casper && chown -R casper:casper /app
USER casper

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3     CMD curl -f http://localhost:3000/health || exit 1

# Run the application
CMD ["npm", "start"]
