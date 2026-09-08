# SaaS / Cloud Deployment Guide

This guide outlines the deployment strategy for hosting the Log Management solution in a public cloud environment (AWS, Azure, GCP) with TLS (HTTPS) enabled.

## Architecture Modifications for SaaS
- **Load Balancer:** A cloud Load Balancer or an Nginx reverse proxy handles TLS termination.
- **Managed Storage:** OpenSearch is replaced with AWS OpenSearch Service or Elastic Cloud for high availability.
- **Container Orchestration:** ECS, EKS, or Cloud Run replaces Docker Compose for deploying the FastAPI backend and Vue.js frontend.

## Enabling TLS (Self-Signed or Let's Encrypt)

If deploying on a single Cloud VM, you can enable HTTPS via Nginx:

1. **Generate Self-Signed Certificate:**
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt
   ```

2. **Update Nginx Configuration (`nginx.conf`):**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-cloud-vm-ip-or-domain;

       ssl_certificate /etc/nginx/ssl/server.crt;
       ssl_certificate_key /etc/nginx/ssl/server.key;

       location / {
           root /usr/share/nginx/html;
           index index.html;
           try_files $uri $uri/ /index.html;
       }

       location /api/ {
           proxy_pass http://backend:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-Proto https;
       }
   }

   server {
       listen 80;
       server_name your-cloud-vm-ip-or-domain;
       return 301 https://$host$request_uri;
   }
   ```

3. **Map SSL Certificates in `docker-compose.yml`:**
   Add a volume mapping under the `frontend` service:
   ```yaml
     frontend:
       volumes:
         - ./server.crt:/etc/nginx/ssl/server.crt:ro
         - ./server.key:/etc/nginx/ssl/server.key:ro
   ```

4. **Restart Stack:**
   ```bash
   docker-compose up -d --build
   ```
