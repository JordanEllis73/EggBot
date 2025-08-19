# ui/Dockerfile
FROM node:18-alpine AS development
# Development stage
WORKDIR /app

# Copy package files
COPY package*.json vite.config.js index.html ./

# Install all dependencies (including dev dependencies)
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Development command - vite.config.js handles host/port
CMD ["npm", "run", "dev"]

# Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production
# Copy built files to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config for API proxying (create this file)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
