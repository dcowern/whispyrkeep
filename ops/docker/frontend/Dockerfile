# WhispyrKeep Frontend Dockerfile
# Angular 18 + Node.js LTS

FROM node:20-alpine

# Set work directory
WORKDIR /app

# Install Angular CLI globally
RUN npm install -g @angular/cli@18

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY frontend/ .

# Create non-root user for security
RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup && \
    chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE 4200

# Default command (overridden in docker-compose)
CMD ["npm", "start", "--", "--host", "0.0.0.0"]
