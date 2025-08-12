# ui/Dockerfile
FROM node:20-alpine AS build
WORKDIR /ui

COPY package*.json vite.config.js index.html ./
COPY src ./src
RUN npm ci

COPY . .

RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /ui/dist /usr/share/nginx/html
EXPOSE 80
