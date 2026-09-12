#!/bin/bash
# generate_certs.sh
# This script generates self-signed certificates for the Log Management SaaS Demo.

CERT_DIR="./certs"

echo "Generating Self-Signed Certificates for SaaS Deployment..."

if [ ! -d "$CERT_DIR" ]; then
    mkdir -p "$CERT_DIR"
fi

# Generate the key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "Certificates generated successfully in the $CERT_DIR directory."
echo "You can now run: docker-compose -f docker-compose.saas.yml up -d"
