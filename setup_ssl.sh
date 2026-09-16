#!/bin/bash
# setup_ssl.sh
# Script to configure real SSL Certificate using Let's Encrypt and certbot

echo "=================================================="
echo "    SSL/TLS Setup Wizard for Log Management SaaS    "
echo "=================================================="

# Check if run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo bash setup_ssl.sh)"
  exit
fi

read -p "Enter your Domain Name (e.g., mylogdemo.duckdns.org): " DOMAIN_NAME
read -p "Enter your Email Address (for certificate renewal alerts): " EMAIL_ADDRESS

if [ -z "$DOMAIN_NAME" ] || [ -z "$EMAIL_ADDRESS" ]; then
    echo "Domain name and email are required. Exiting."
    exit 1
fi

echo "Installing Certbot..."
apt update && apt install -y certbot

echo "Requesting SSL Certificate for $DOMAIN_NAME..."
# Stop frontend temporarily to free port 80 for standalone verification
docker compose -f docker-compose.saas.yml stop frontend

certbot certonly --standalone -d "$DOMAIN_NAME" --non-interactive --agree-tos -m "$EMAIL_ADDRESS"

if [ $? -eq 0 ]; then
    echo "Certificate successfully generated!"
    echo "Copying certificates to ./certs directory..."
    
    mkdir -p ./certs
    cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem ./certs/server.crt
    cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem ./certs/server.key
    
    # Update nginx config to use the domain name if needed
    sed -i "s/server_name _;/server_name $DOMAIN_NAME;/g" frontend/nginx.saas.conf
    
    echo "Restarting frontend container..."
    docker compose -f docker-compose.saas.yml start frontend
    
    echo "=================================================="
    echo "SUCCESS! You can now access your dashboard securely at:"
    echo "https://$DOMAIN_NAME"
    echo "=================================================="
else
    echo "Failed to generate certificate. Please check your domain DNS settings (it must point to this server's public IP)."
    docker compose -f docker-compose.saas.yml start frontend
fi
