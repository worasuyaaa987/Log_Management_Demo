# Log Management Demo - Frontend

This is the Vue.js 3 Single Page Application (SPA) for the Log Management Demo.

## Tech Stack
- **Framework:** Vue 3 (Composition API / `<script setup>`)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Visualization:** Chart.js (via `vue-chartjs`)

## Features
- **Real-time Search & Filtering:** Interfaces directly with the FastAPI backend to query OpenSearch.
- **Data Visualization:** Displays a timeline chart of events and top statistics (IPs, Users, Events).
- **Multi-Tenant Support:** JWT tokens enforce Role-Based Access Control, ensuring users only see their tenant's logs.
- **Alert Dashboard:** Displays recent security alerts (e.g., Brute Force attacks) captured by the backend workers.

## Local Development Setup

```bash
# Install dependencies
npm install

# Run the development server (requires backend to be running on port 8000)
npm run dev
```

For production deployment, this frontend is built as static files and served via Nginx (see `Dockerfile` and `docker-compose.yml`).
