/**
 * ShopStream API Client
 *
 * REST API client for fetching analytics data from the backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

/**
 * Get live metrics for the last N minutes
 */
export const getLiveMetrics = async (minutes = 5) => {
  return await api.get(`/api/metrics/live?minutes=${minutes}`);
};

/**
 * Get revenue trend over time
 */
export const getRevenueTrend = async (hours = 1) => {
  return await api.get(`/api/metrics/revenue?hours=${hours}`);
};

/**
 * Get trending products
 */
export const getTrendingProducts = async (limit = 10, minutes = 5) => {
  return await api.get(`/api/metrics/products/trending?limit=${limit}&minutes=${minutes}`);
};

/**
 * Get conversion funnel metrics
 */
export const getConversionFunnel = async (hours = 1) => {
  return await api.get(`/api/metrics/funnel?hours=${hours}`);
};

/**
 * Get geographic distribution
 */
export const getGeographicDistribution = async (limit = 10, hours = 1) => {
  return await api.get(`/api/metrics/geographic?limit=${limit}&hours=${hours}`);
};

/**
 * Get active alerts
 */
export const getAlerts = async (limit = 10) => {
  return await api.get(`/api/metrics/alerts?limit=${limit}`);
};

/**
 * Get hourly comparison
 */
export const getHourlyComparison = async () => {
  return await api.get(`/api/metrics/comparison`);
};

/**
 * Health check
 */
export const healthCheck = async () => {
  return await api.get('/api/metrics/health');
};

export default api;
