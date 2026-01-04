/**
 * ShopStream Dashboard Component
 *
 * Main dashboard that displays real-time analytics.
 * Connects to WebSocket for live updates.
 */

import React, { useState, useEffect } from 'react';
import wsClient from '../utils/websocket';
import { formatTimestamp, getLocation } from '../utils/timezone';
import MetricCard from './MetricCard';
import LiveChart from './LiveChart';
import TrendingProducts from './TrendingProducts';
import ConversionFunnel from './ConversionFunnel';
import Alerts from './Alerts';
import GeographicChart from './GeographicChart';

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Connect to WebSocket
    wsClient.connect();

    // Listen for messages
    const unsubscribe = wsClient.addListener((data) => {
      if (data.type === 'metrics_update') {
        setMetrics(data.data);
        // Ensure timestamp is interpreted as UTC by appending 'Z' if missing
        const timestamp = data.timestamp.endsWith('Z') ? data.timestamp : data.timestamp + 'Z';
        setLastUpdate(new Date(timestamp));
      } else if (data.type === 'connection') {
        setIsConnected(data.status === 'connected');
      }
    });

    // Cleanup on unmount
    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, []);

  // Format revenue with $ and commas
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  // Format numbers with commas
  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value || 0);
  };

  // Format percentage
  const formatPercent = (value) => {
    const num = parseFloat(value) || 0;
    return num >= 0 ? `+${num.toFixed(1)}%` : `${num.toFixed(1)}%`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                ShopStream
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Real-Time E-Commerce Analytics • Built by Harsha Kanaparthi • {getLocation()}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {isConnected ? 'Live' : 'Disconnected'}
                </span>
              </div>
              {/* Last Update */}
              {lastUpdate && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Updated {formatTimestamp(lastUpdate)}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!metrics ? (
          /* Loading State */
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">
                Connecting to real-time analytics...
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <MetricCard
                title="Revenue (Last Hour)"
                value={formatCurrency(metrics.comparison?.current_revenue || 0)}
                change={formatPercent(metrics.comparison?.revenue_change_percent || 0)}
                isPositive={(metrics.comparison?.revenue_change_percent || 0) >= 0}
                icon="💰"
              />
              <MetricCard
                title="Orders (Last Hour)"
                value={formatNumber(metrics.comparison?.current_orders || 0)}
                change={formatPercent(metrics.comparison?.orders_change_percent || 0)}
                isPositive={(metrics.comparison?.orders_change_percent || 0) >= 0}
                icon="🛒"
              />
              <MetricCard
                title="Active Users"
                value={formatNumber(metrics.live?.active_users || 0)}
                icon="👥"
              />
            </div>

            {/* Live Sales Chart */}
            <div className="metric-card">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                📊 Sales Per Minute (Live)
              </h2>
              <LiveChart data={metrics.revenue_trend || []} />
            </div>

            {/* Trending Products */}
            <div className="metric-card">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                🔥 Trending Products (Right Now)
              </h2>
              <TrendingProducts products={metrics.trending_products || []} />
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Conversion Funnel */}
              <div className="metric-card">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  📈 Conversion Funnel
                </h2>
                <ConversionFunnel data={metrics.funnel || {}} />
              </div>

              {/* Alerts */}
              <div className="metric-card">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  ⚠️ Alerts
                </h2>
                <Alerts alerts={metrics.alerts || []} />
              </div>
            </div>

            {/* Geographic Distribution */}
            <div className="metric-card">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                🗺️ Geographic Sales
              </h2>
              <GeographicChart data={metrics.geographic || []} />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            ShopStream v1.0 • Built by Harsha Kanaparthi • Powered by Kafka, Spark, TimescaleDB, FastAPI & React
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Dashboard;
