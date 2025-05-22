#!/bin/bash

echo "Starting Key-Value Store Distributed System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Make sure the script is executable
chmod +x ./start.sh

# Build and start the services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 15

echo "System is running! Access the API at http://localhost:80"
echo "RabbitMQ management interface available at http://localhost:15672 (guest/guest)"
echo "CockroachDB admin interfaces:"
echo "- Node 1: http://localhost:8080"
echo "- Node 2: http://localhost:8081"
echo "- Node 3: http://localhost:8082"
echo ""
echo "Redis High Availability Setup:"
echo "- Master: localhost:6380"
echo "- Replica: localhost:6381"
echo "- Envoy Proxy (entry point for apps): localhost:6378"
echo "- Envoy Admin: http://localhost:9901"
echo ""
echo "HAProxy está balanceando conexões ao CockroachDB na porta 26256."
echo ""
echo "Para verificar o status do cluster CockroachDB:"
echo "docker exec -it \$(docker ps | grep crdb1 | awk '{print \$1}') /cockroach/cockroach node status --insecure"
echo ""
echo "Para verificar o status da replicação Redis:"
echo "docker exec -it \$(docker ps | grep redis-replica | awk '{print \$1}') redis-cli info replication"
echo ""
echo "To test the API, you can use these commands:"
echo "PUT: curl -X PUT http://localhost/ -H 'Content-Type: application/json' -d '{\"data\": {\"key\": \"test-key\", \"value\": \"test-value\"}}'"
echo "GET: curl -X GET http://localhost/test-key"
echo "DELETE: curl -X DELETE http://localhost/test-key"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop the system: docker-compose down"