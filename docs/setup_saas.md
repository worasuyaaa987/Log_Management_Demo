# SaaS / Cloud Deployment Guide

This guide outlines the deployment strategy for hosting the Log Management solution in a public cloud environment (AWS, Azure, GCP) with TLS (HTTPS) enabled.

## Architecture Modifications for SaaS
- **Load Balancer / Nginx:** Nginx handles TLS termination locally, or you can place a cloud Load Balancer in front.
- **Managed Storage:** OpenSearch can be replaced with AWS OpenSearch Service or Elastic Cloud for high availability.
- **Container Orchestration:** ECS, EKS, or Cloud Run replaces Docker Compose for deploying the FastAPI backend and Vue.js frontend at scale.

## Enabling TLS and SaaS Mode (Local/VM)

We provide a dedicated `docker-compose.saas.yml` to demonstrate the SaaS mode with HTTPS securely enabled via Nginx.

1. **Generate Self-Signed Certificate:**
   Run the provided helper script to generate the certificates:
   ```bash
   # Windows (Git Bash/WSL) or Linux/macOS
   bash generate_certs.sh
   ```
   *This will create a `certs/` directory with `server.crt` and `server.key`.*

2. **Start the SaaS Stack:**
   Use the SaaS-specific compose file which mounts the custom `nginx.saas.conf` and certificates:
   ```bash
   docker-compose -f docker-compose.saas.yml up -d --build
   ```

3. **Verify HTTPS:**
   Navigate to **[https://localhost](https://localhost)**. 
   *(Note: Because it is a self-signed certificate, your browser will show a security warning. You can safely proceed/accept the risk for this demonstration).*
   All HTTP traffic on port 80 will automatically redirect to HTTPS on port 443.
