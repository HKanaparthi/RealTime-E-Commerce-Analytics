/**
 * GeographicChart Component
 * Displays geographic sales distribution with bar chart
 */

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function GeographicChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500 dark:text-gray-400">No geographic data available</p>
      </div>
    );
  }

  // Format data for chart (top 10 locations)
  const chartData = data.slice(0, 10).map(location => ({
    location: `${location.city}, ${location.country}`,
    revenue: parseFloat(location.revenue) || 0,
    orders: location.orders || 0,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            {payload[0].payload.location}
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
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
          <XAxis
            type="category"
            dataKey="location"
            stroke="#6B7280"
            tick={{ fill: '#6B7280', fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={120}
          />
          <YAxis
            type="number"
            stroke="#6B7280"
            tick={{ fill: '#6B7280', fontSize: 12 }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="revenue"
            fill="#3B82F6"
            radius={[8, 8, 0, 0]}
            animationDuration={300}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default GeographicChart;
