<template>
  <div class="dashboard-container">
    <header class="glass-panel mb-2">
      <h1>Demo Log Management System</h1>
      <p class="text-muted">Multi-tenant Cloud & Appliance Security Analytics</p>
    </header>

    <!-- Filters -->
    <section class="glass-panel mb-2 filters">
      <div class="filter-group">
        <label>Tenant</label>
        <select v-model="filters.tenant" class="input-field" @change="loadData">
          <option value="all">All Tenants</option>
          <option value="demoA">Demo A</option>
          <option value="demoB">Demo B</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Time Range</label>
        <select v-model="filters.timeRange" class="input-field" @change="loadData">
          <option value="1h">Last 1 Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
        </select>
      </div>
      <button class="btn" @click="loadData">Refresh Data</button>
    </section>

    <!-- Summary Cards -->
    <section class="summary-cards mb-2">
      <div class="glass-panel card">
        <h3>Total Logs</h3>
        <p class="big-stat">{{ data.total.toLocaleString() }}</p>
      </div>
      <div class="glass-panel card">
        <h3>Active Tenants</h3>
        <p class="big-stat">{{ data.active_tenants }}</p>
      </div>
      <div class="glass-panel card danger-card">
        <h3>Active Alerts</h3>
        <p class="big-stat danger-text">{{ data.alerts }}</p>
      </div>
    </section>

    <!-- Charts -->
    <section class="charts mb-2">
      <div class="glass-panel chart-container">
        <h3>Event Timeline</h3>
        <div class="chart-wrapper">
          <Line v-if="chartDataLoaded" :data="timelineChartData" :options="chartOptions" />
        </div>
      </div>
      <div class="glass-panel chart-container">
        <h3>Top IPs</h3>
        <div class="chart-wrapper">
          <Bar v-if="chartDataLoaded" :data="topIpsChartData" :options="chartOptions" />
        </div>
      </div>
    </section>

    <!-- Logs Table -->
    <section class="glass-panel">
      <h3>Recent Logs</h3>
      <div class="table-responsive">
        <table class="log-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Tenant</th>
              <th>Source</th>
              <th>Event</th>
              <th>User</th>
              <th>Src IP</th>
              <th>Dst IP</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in data.logs" :key="log.id">
              <td>{{ new Date(log.timestamp).toLocaleString() }}</td>
              <td><span class="badge">{{ log.tenant }}</span></td>
              <td>{{ log.source }}</td>
              <td>{{ log.event_type }}</td>
              <td>{{ log.user || '-' }}</td>
              <td>{{ log.src_ip || '-' }}</td>
              <td>{{ log.dst_ip || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { fetchLogs } from '../api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line, Bar } from 'vue-chartjs';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// State
const filters = ref({
  tenant: 'all',
  timeRange: '24h'
});

const data = ref({
  total: 0,
  active_tenants: 0,
  alerts: 0,
  timeline: [],
  top_ips: [],
  logs: []
});

const chartDataLoaded = ref(false);

const loadData = async () => {
  chartDataLoaded.value = false;
  const res = await fetchLogs(filters.value.tenant, filters.value.timeRange);
  data.value = res;
  chartDataLoaded.value = true;
};

onMounted(() => {
  loadData();
});

// Chart.js Theme Options for Dark Mode
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#f8fafc' }
    }
  },
  scales: {
    x: {
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(255, 255, 255, 0.05)' }
    },
    y: {
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(255, 255, 255, 0.05)' }
    }
  }
};

const timelineChartData = computed(() => {
  return {
    labels: data.value.timeline.map(item => item.time),
    datasets: [
      {
        label: 'Log Events',
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        data: data.value.timeline.map(item => item.count),
        fill: true,
        tension: 0.4
      }
    ]
  };
});

const topIpsChartData = computed(() => {
  return {
    labels: data.value.top_ips.map(item => item.ip),
    datasets: [
      {
        label: 'Connections',
        backgroundColor: '#10b981',
        data: data.value.top_ips.map(item => item.count)
      }
    ]
  };
});
</script>

<style scoped>
.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
}

.mb-2 {
  margin-bottom: 1.5rem;
}

.text-muted {
  color: var(--text-muted);
}

.filters {
  display: flex;
  gap: 1.5rem;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.card h3 {
  color: var(--text-muted);
  font-size: 1rem;
}

.big-stat {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-main);
}

.danger-text {
  color: var(--danger);
}

.danger-card {
  border-color: rgba(239, 68, 68, 0.3);
}

.charts {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 900px) {
  .charts {
    grid-template-columns: 1fr;
  }
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

.table-responsive {
  overflow-x: auto;
}

.badge {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
