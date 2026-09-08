<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <!-- Navigation -->
    <nav class="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
      <div class="flex items-center space-x-4">
        <div class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400">
          Demo Log Management
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <select v-model="timeRange" @change="fetchData" class="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5">
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
        </select>
        <button @click="logout" class="text-sm text-gray-400 hover:text-white transition-colors">Logout</button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="p-6 max-w-7xl mx-auto space-y-6">
      
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm">
          <h3 class="text-gray-400 text-sm font-medium">Total Logs</h3>
          <p class="text-3xl font-bold mt-2">{{ dashboardData.total?.toLocaleString() || 0 }}</p>
        </div>
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm">
          <h3 class="text-gray-400 text-sm font-medium">Active Tenants</h3>
          <p class="text-3xl font-bold mt-2">{{ dashboardData.active_tenants || 0 }}</p>
        </div>
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm">
          <h3 class="text-gray-400 text-sm font-medium">Active Alerts</h3>
          <p class="text-3xl font-bold mt-2 text-red-400">{{ dashboardData.alerts_count || 0 }}</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm h-80">
          <h3 class="text-gray-400 text-sm font-medium mb-4">Event Timeline</h3>
          <div class="h-64 relative w-full">
            <Line v-if="chartData.labels" :data="chartData" :options="chartOptions" />
            <div v-else class="flex items-center justify-center h-full text-gray-600">Loading chart...</div>
          </div>
        </div>
        
        <!-- Alerts Panel -->
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm h-80 overflow-auto">
          <h3 class="text-gray-400 text-sm font-medium mb-4 text-red-400 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            Recent Alerts
          </h3>
          <ul class="space-y-3">
            <li v-for="alert in dashboardData.alert_messages" :key="alert['@timestamp']" class="bg-red-900/20 border border-red-900/50 p-3 rounded-lg">
              <div class="text-xs text-red-400 font-bold mb-1">{{ alert.rule_name }}</div>
              <div class="text-sm text-gray-300">{{ alert.description }}</div>
              <div class="text-xs text-gray-500 mt-2">{{ formatDate(alert['@timestamp']) }}</div>
            </li>
            <li v-if="!dashboardData.alert_messages?.length" class="text-sm text-gray-600 text-center py-4">No recent alerts</li>
          </ul>
        </div>
      </div>

      <!-- Top Stats Row -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Top IPs -->
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm h-64 overflow-auto">
          <h3 class="text-gray-400 text-sm font-medium mb-4">Top Source IPs</h3>
          <ul class="space-y-3">
            <li v-for="item in dashboardData.top_ips" :key="item.key" class="flex justify-between items-center">
              <span class="text-sm font-mono text-blue-300">{{ item.key }}</span>
              <span class="text-sm text-gray-400 bg-gray-800 px-2 py-1 rounded">{{ item.count }}</span>
            </li>
            <li v-if="!dashboardData.top_ips?.length" class="text-sm text-gray-600 text-center py-4">No data</li>
          </ul>
        </div>
        
        <!-- Top Users -->
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm h-64 overflow-auto">
          <h3 class="text-gray-400 text-sm font-medium mb-4">Top Users</h3>
          <ul class="space-y-3">
            <li v-for="item in dashboardData.top_users" :key="item.key" class="flex justify-between items-center">
              <span class="text-sm text-purple-300">{{ item.key }}</span>
              <span class="text-sm text-gray-400 bg-gray-800 px-2 py-1 rounded">{{ item.count }}</span>
            </li>
            <li v-if="!dashboardData.top_users?.length" class="text-sm text-gray-600 text-center py-4">No data</li>
          </ul>
        </div>

        <!-- Top Event Types -->
        <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-sm h-64 overflow-auto">
          <h3 class="text-gray-400 text-sm font-medium mb-4">Top Event Types</h3>
          <ul class="space-y-3">
            <li v-for="item in dashboardData.top_events" :key="item.key" class="flex justify-between items-center">
              <span class="text-sm text-teal-300">{{ item.key }}</span>
              <span class="text-sm text-gray-400 bg-gray-800 px-2 py-1 rounded">{{ item.count }}</span>
            </li>
            <li v-if="!dashboardData.top_events?.length" class="text-sm text-gray-600 text-center py-4">No data</li>
          </ul>
        </div>
      </div>

      <!-- Recent Logs Table -->
      <div class="bg-gray-900 rounded-xl border border-gray-800 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
          <h3 class="text-gray-400 text-sm font-medium">Recent Logs</h3>
          <button @click="fetchData" class="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center space-x-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            <span>Refresh</span>
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-left text-gray-400">
            <thead class="text-xs text-gray-500 uppercase bg-gray-800/50">
              <tr>
                <th scope="col" class="px-6 py-3">Timestamp</th>
                <th scope="col" class="px-6 py-3">Tenant</th>
                <th scope="col" class="px-6 py-3">Source</th>
                <th scope="col" class="px-6 py-3">Event Type</th>
                <th scope="col" class="px-6 py-3">User</th>
                <th scope="col" class="px-6 py-3">Src IP</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in dashboardData.logs" :key="log.id" class="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap font-mono text-xs">{{ formatDate(log.timestamp) }}</td>
                <td class="px-6 py-4"><span class="bg-indigo-900/50 text-indigo-300 px-2 py-1 rounded text-xs border border-indigo-800">{{ log.tenant }}</span></td>
                <td class="px-6 py-4">{{ log.source }}</td>
                <td class="px-6 py-4 text-blue-300">{{ log.event_type }}</td>
                <td class="px-6 py-4">{{ log.user }}</td>
                <td class="px-6 py-4 font-mono">{{ log.src_ip }}</td>
              </tr>
              <tr v-if="!dashboardData.logs?.length">
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">No logs found in this time range. Try running the simulation script.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

// Chart.js setup
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const timeRange = ref('24h')
const dashboardData = ref({})

// Fetch data
const fetchData = async () => {
  try {
    const res = await api.get(`/search?timeRange=${timeRange.value}`)
    dashboardData.value = res.data
  } catch (error) {
    if (error.response?.status === 401) {
      logout()
    }
    console.error('Failed to fetch data', error)
  }
}

// Chart configuration
const chartData = computed(() => {
  const timeline = dashboardData.value.timeline || []
  return {
    labels: timeline.map(item => item.time),
    datasets: [
      {
        label: 'Log Events',
        data: timeline.map(item => item.count),
        borderColor: '#3b82f6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#3b82f6'
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      mode: 'index',
      intersect: false,
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      titleColor: '#fff',
      bodyColor: '#e5e7eb',
      borderColor: '#374151',
      borderWidth: 1
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: '#374151', drawBorder: false },
      ticks: { color: '#9ca3af' }
    },
    x: {
      grid: { display: false, drawBorder: false },
      ticks: { color: '#9ca3af', maxTicksLimit: 8 }
    }
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  }
}

// Utilities
const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString()
  } catch (e) {
    return dateStr
  }
}

onMounted(() => {
  fetchData()
  // Auto refresh every 30 seconds
  setInterval(fetchData, 30000)
})
</script>
