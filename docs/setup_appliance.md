# Appliance Mode Setup Guide

This mode runs the entire Log Management stack on a single server or Virtual Machine using Docker Compose.

## Prerequisites
- Ubuntu 22.04+ (or equivalent Linux distro)
- 4 vCPU, 8 GB RAM, 40 GB Disk
- Docker and Docker Compose installed
- Ports `80` (HTTP), `514` (Syslog TCP/UDP) open

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
   Use the provided start script or docker-compose directly:
   ```bash
   ./start_demo.sh
   # or
   docker-compose up -d --build
   ```

4. **Verify Deployment**
   - Check container status: `docker-compose ps`
   - All 4 containers (`opensearch`, `backend`, `frontend`, `fluentbit`) should be running.

5. **Access the System**
   - **Dashboard UI:** Open a web browser to `http://<your-server-ip>`
   - **Login:** Use `admin` / `admin123` or `viewerA` / `viewer123`
   
6. **Ingest Test Data**
   Run the sample script to populate the dashboard:
   ```bash
   python samples/post_logs.py
   ```
