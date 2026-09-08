import axios from 'axios';

// We assume the frontend will be served by Nginx which proxies /api to the backend
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

export const fetchLogs = async (tenant, timeRange) => {
  try {
    const response = await apiClient.get('/search', {
      params: { tenant, timeRange }
    });
    return response.data;
  } catch (error) {
    console.warn("Backend not reachable or returned error. Using mock data for demo.");
    return {
      total: 15420,
      active_tenants: 4,
      alerts: 3,
      timeline: [
        { time: '10:00', count: 120 },
        { time: '11:00', count: 300 },
        { time: '12:00', count: 150 },
        { time: '13:00', count: 400 },
        { time: '14:00', count: 210 },
        { time: '15:00', count: 500 },
        { time: '16:00', count: 100 }
      ],
      top_ips: [
        { ip: '10.0.1.10', count: 450 },
        { ip: '8.8.8.8', count: 320 },
        { ip: '203.0.113.7', count: 210 },
        { ip: '192.168.1.50', count: 150 }
      ],
      logs: [
        { id: 1, timestamp: '2026-09-08T10:00:00Z', tenant: 'demoA', source: 'firewall', event_type: 'deny', src_ip: '10.0.1.10', dst_ip: '8.8.8.8' },
        { id: 2, timestamp: '2026-09-08T10:05:00Z', tenant: 'demoA', source: 'api', event_type: 'login_failed', user: 'alice', src_ip: '203.0.113.7' },
        { id: 3, timestamp: '2026-09-08T10:15:00Z', tenant: 'demoB', source: 'm365', event_type: 'UserLoggedIn', user: 'bob@demo.local', src_ip: '198.51.100.23' },
        { id: 4, timestamp: '2026-09-08T10:20:00Z', tenant: 'demoB', source: 'aws', event_type: 'CreateUser', user: 'admin', src_ip: '-' }
      ]
    };
  }
};
