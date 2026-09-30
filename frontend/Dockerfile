FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Rewrites are resolved at build time
ARG BACKEND_SERVICE=http://127.0.0.1:8000
ENV BACKEND_SERVICE=$BACKEND_SERVICE
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm", "start"]
