# SaaS / Cloud Deployment Guide

This guide outlines the deployment strategy for hosting the Log Management solution in a public cloud environment (AWS, Azure, GCP) with TLS (HTTPS) enabled.

## Pre-Production Architecture Modifications (SaaS Mode)
- **Message Queue (Redis):** A single Redis instance buffers normal incoming logs in a list (`logs_queue`) to prevent OpenSearch bottlenecks during traffic spikes. Security events bypass the queue via a fast-lane path for instant alerting.
- **Enrichment Engine:** The background worker (`redis_worker`) automatically enriches incoming IP addresses with GeoIP country mapping using `ip-api.com` (free tier) with an in-memory Python dict cache before bulk-inserting into OpenSearch.
- **Automated Retention (ISM):** The `init_retention.sh` script automatically applies a 7-day deletion policy for disk space management.
- **Let's Encrypt SSL Prep:** We have prepared `setup_ssl.sh` for easy migration to a real SSL certificate once a domain is registered (e.g., via DuckDNS).
- **CI/CD Pipeline:** Integrated GitHub Actions workflow for continuous testing of backend components.
- **Load Balancer / Nginx:** Nginx handles TLS termination locally, or you can place a cloud Load Balancer in front.

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

---

## Cloud Deployment Guide (Public URL)

This section provides step-by-step instructions to deploy the system on a cloud VM so that reviewers can access it via a public URL.

### Prerequisites
- A cloud provider account (DigitalOcean, AWS, or Google Cloud)
- Basic familiarity with SSH and Linux terminal
- The project source code (via `git clone`)

---

### Step 1: Create a Cloud VM

Choose one of the following providers. Minimum specs: **4 GB RAM, 2 vCPU, 40 GB disk** (OpenSearch requires at least 2 GB heap).

#### Option A: DigitalOcean Droplet (Recommended)
1. Sign up at [https://cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Create → Droplets
3. Configuration:
   - **Region:** Singapore (sgp1)
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic → Regular → $24/mo (4 GB RAM, 2 vCPU)
   - **Authentication:** SSH Key (recommended) or Password
4. Note the **public IP address** (e.g., `159.89.194.xxx`)

#### Option B: AWS Lightsail
1. Go to [https://lightsail.aws.amazon.com](https://lightsail.aws.amazon.com)
2. Create instance
3. Configuration:
   - **Region:** ap-southeast-1 (Singapore)
   - **Platform:** Linux/Unix → Ubuntu 22.04 LTS
   - **Plan:** $20/mo (4 GB RAM, 2 vCPU)
4. Networking tab → Create & attach a **Static IP**

#### Option C: Google Cloud Compute Engine
1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Compute Engine → VM Instances → Create Instance
3. Configuration:
   - **Region:** asia-southeast1 (Singapore)
   - **Machine type:** e2-medium (2 vCPU, 4 GB)
   - **Boot disk:** Ubuntu 22.04 LTS, 40 GB
   - **Firewall:** ✅ Allow HTTP traffic, ✅ Allow HTTPS traffic
4. Note the **External IP**

---

### Step 2: Configure Firewall

Open these ports in your cloud provider's firewall/security group:

| Port | Protocol | Purpose                    |
|------|----------|----------------------------|
| 22   | TCP      | SSH access                 |
| 80   | TCP      | HTTP (redirects to HTTPS)  |
| 443  | TCP      | HTTPS (Dashboard UI)       |
| 514  | TCP/UDP  | Syslog ingestion (optional)|

**DigitalOcean:** Networking → Firewalls → Create Firewall → Add rules → Apply to Droplet  
**AWS Lightsail:** Instance → Networking → Add rules  
**Google Cloud:** VPC Network → Firewall rules → Create rule

---

### Step 3: SSH into VM and Install Docker

```bash
# Connect to your VM (replace with your IP)
ssh root@YOUR_VM_IP

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo apt install docker-compose -y

# Configure OpenSearch kernel requirement
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Install Git
sudo apt install git -y

# Verify installation
docker --version        # Expected: Docker version 24.x+
docker-compose --version # Expected: docker-compose version 1.29+
```

---

### Step 4: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/worasuyaaa987/Log_Management_Demo.git
cd Log_Management_Demo

# Create .env from template
cp .env.example .env

# Edit the .env file for production
nano .env
```

Update `.env` with strong credentials:
```env
# OpenSearch Configuration
OPENSEARCH_URL=https://opensearch:9200
OPENSEARCH_INITIAL_ADMIN_PASSWORD=YourStrongPassword123!

# Backend FastAPI Configuration
SECRET_KEY=change_this_to_a_long_secure_random_string_in_production
INGEST_TOKEN=your_secure_ingest_token
WEBHOOK_URL=
API_PORT=8000
```

Save with `Ctrl+O` → Enter, then exit with `Ctrl+X`.

---

### Step 5: Generate SSL Certificate and Deploy

```bash
# Generate self-signed SSL certificates
bash generate_certs.sh

# Build and start all containers in SaaS mode
docker-compose -f docker-compose.saas.yml up -d --build
```

> First build takes approximately 3–5 minutes to download images and compile the frontend.

Verify all containers are running:
```bash
docker-compose -f docker-compose.saas.yml ps
```

Expected output (all should show **Up**):
```
NAME                    STATUS
demo_opensearch_saas    Up      0.0.0.0:9200->9200/tcp
demo_redis_saas         Up      0.0.0.0:6379->6379/tcp
demo_backend_saas       Up      0.0.0.0:8000->8000/tcp
demo_fluentbit_saas     Up      0.0.0.0:514->514/tcp, 514/udp
demo_frontend_saas      Up      0.0.0.0:80->80/tcp, 443/tcp
```

If any container fails, check logs:
```bash
docker-compose -f docker-compose.saas.yml logs <service_name>
```

---

### Step 6: Initialize Retention Policy and Seed Data

```bash
# Wait for OpenSearch to fully start
sleep 30

# Apply 7-day ISM retention policy
bash init_retention.sh

# Install Python requests library for the simulator
apt install python3-pip -y
pip3 install requests

# Run the log simulator to populate sample data
python3 samples/post_logs.py
```

---

### Step 7: Set Up a Free Domain Name (Optional)

Instead of sharing a raw IP address, set up a free subdomain:

1. Go to [https://www.duckdns.org](https://www.duckdns.org)
2. Sign in with GitHub or Google
3. Create a subdomain (e.g., `log-demo`) → Result: `log-demo.duckdns.org`
4. Enter your VM's **public IP address** → Click **Update IP**
5. Your system is now accessible at `https://log-demo.duckdns.org` (Still with a self-signed warning).

#### Upgrade to Real SSL (Let's Encrypt)
Once your DuckDNS domain is ready, you can get a valid SSL certificate (green padlock) by running:
```bash
sudo bash setup_ssl.sh
```
Follow the interactive prompts to enter your domain name and email address. The script will automatically request the certificate and restart the Nginx server.

---

### Step 8: Verify the Deployment

From your **local machine** (not the VM), open a browser:

```
https://YOUR_VM_IP
```
or (if using DuckDNS):
```
https://log-demo.duckdns.org
```

> The browser will warn about the self-signed certificate. Click **Advanced** → **Proceed** to continue.

**Test credentials:**

| Username | Password | Role | Tenant Access |
|----------|----------|------|---------------|
| `admin` | `admin123` | Admin | All tenants |
| `viewerA` | `viewer123` | Viewer | `demoA` only |
| `viewerB` | `viewer123` | Viewer | `demoB` only |

**Verify API access:**
```bash
# Get a JWT token
curl -k -X POST https://YOUR_VM_IP/token \
  -d "username=admin&password=admin123"

# Expected response:
# {"access_token": "eyJ...", "token_type": "bearer"}
```

---

### Troubleshooting

| Problem | Solution |
|---------|----------|
| OpenSearch fails to start | Check `vm.max_map_count`: `sysctl vm.max_map_count` (must be ≥ 262144) |
| Port 443 not reachable | Verify firewall rules allow inbound TCP 443 |
| Backend returns 500 | Check backend logs: `docker logs demo_backend_saas` |
| Dashboard shows no data | Run the simulator: `python3 samples/post_logs.py` |
| Certificate errors in curl | Use the `-k` flag to skip certificate verification |

---

### Cleanup (After Review)

To avoid ongoing charges, **delete the VM** after the review is complete:

- **DigitalOcean:** Droplet → Destroy → Confirm
- **AWS Lightsail:** Instance → Delete
- **Google Cloud:** VM Instances → Select → Delete
