/**
 * LiveChart Component
 * Real-time line chart showing sales per minute
 */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatChartTime } from '../utils/timezone';

function LiveChart({ data }) {
  // Format timestamp for display in Eastern Time
  const formatTime = (timestamp) => {
    // Ensure timestamp is interpreted as UTC by appending 'Z' if missing
    const utcTimestamp = timestamp.endsWith('Z') ? timestamp : timestamp + 'Z';
    return formatChartTime(utcTimestamp);
  };

  // Format data for chart
  const chartData = (data || []).map(item => ({
    time: formatTime(item.timestamp),
    revenue: parseFloat(item.revenue) || 0,
    orders: item.orders || 0,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {payload[0].payload.time}
          </p>
          <p className="text-sm text-green-600 dark:text-green-400">
            Revenue: ${payload[0].value.toFixed(2)}
          </p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            Orders: {payload[0].payload.orders}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64">
      {chartData.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500 dark:text-gray-400">No data available</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
            <XAxis
              dataKey="time"
              stroke="#6B7280"
              tick={{ fill: '#6B7280', fontSize: 12 }}
            />
            <YAxis
              stroke="#6B7280"
              tick={{ fill: '#6B7280', fontSize: 12 }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#10B981"
              strokeWidth={2}
              dot={{ fill: '#10B981', r: 3 }}
              activeDot={{ r: 5 }}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export default LiveChart;
