# Use an official Node.js runtime as the base image
FROM node:16 AS build

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json first to optimize rebuilding the Docker image
COPY . /app

# Start with the official Nginx image as it's lightweight and serves static content quickly
FROM nginx:alpine

# Copy the build folder from the above step to the Nginx default location
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80 of the container
EXPOSE 80

# Command to run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]