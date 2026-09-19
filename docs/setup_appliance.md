# Appliance Mode Setup Guide

This mode runs the entire Log Management stack on a single server or Virtual Machine using Docker Compose.

## Prerequisites
- Ubuntu 22.04+ (or equivalent Linux distro), or Windows 10/11 with Docker Desktop
- 4 vCPU, 8 GB RAM, 40 GB Disk
- Docker and Docker Compose installed
- Ports open:
  | Port | Protocol | Purpose |
  |------|----------|---------|
  | 80 | TCP | HTTP (Dashboard UI) |
  | 514 | TCP/UDP | Syslog ingestion |
  | 8000 | TCP | FastAPI Backend (optional, for debugging) |
  | 9200 | TCP | OpenSearch (optional, for debugging) |

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/log-management-demo.git
   cd log-management-demo
   ```

2. **Configure Environment Variables**
   Copy the example file to `.env` and set secure passwords if necessary.
   ```bash
   cp .env.example .env
   ```

3. **Start the Appliance**

   **For Linux / macOS:**
   ```bash
   ./start_demo.sh
   ```

   **For Windows (PowerShell or CMD):**
   ```cmd
   .\start_demo.bat
   ```

   **Manual Start (any OS):**
   ```bash
   docker-compose up -d --build
   ```

4. **Verify Deployment**
   - Check container status: `docker-compose ps`
   - All 5 containers should be running:

   | Container Name | Service | Description |
   |----------------|---------|-------------|
   | `demo_opensearch` | opensearch | Storage & search engine |
   | `demo_redis` | redis | Message queue buffer |
   | `demo_backend` | backend | FastAPI API server |
   | `demo_frontend` | frontend | Nginx + Vue.js SPA |
   | `demo_fluentbit` | fluent-bit | Log collector (Syslog + file tail) |

5. **Access the System**
   - **Dashboard UI:** Open a web browser to `http://<your-server-ip>`
   - **Login credentials:**
     | Username | Password | Role | Tenant Access |
     |----------|----------|------|---------------|
     | `admin` | `admin123` | Admin | All tenants |
     | `viewerA` | `viewer123` | Viewer | `demoA` only |
     | `viewerB` | `viewer123` | Viewer | `demoB` only |
   
6. **Ingest Test Data**
   Run the sample script to populate the dashboard:
   ```bash
   python samples/post_logs.py
   ```

7. **Initialize Retention Policy**
   Apply the 7-day automatic log deletion policy:
   ```bash
   bash init_retention.sh
   ```
   > **Note (Windows):** The `start_demo.bat` script does not automatically apply the retention policy. Open Git Bash or WSL and run `bash init_retention.sh` manually.

8. **Test Alerting (Optional)**
   Trigger a Brute Force Attack alert to verify the alerting system:
   ```bash
   python samples/trigger_alert.py
   ```

