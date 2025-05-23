#!/bin/bash

echo "Starting Key-Value Store Distributed System..."

# Make sure the script is executable
chmod +x ./start.sh

# Build and start the services
echo "Building and starting services..."
docker-compose up --build -d
