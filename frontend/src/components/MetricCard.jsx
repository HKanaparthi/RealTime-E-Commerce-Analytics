/**
 * MetricCard Component
 * Displays a single metric with value, change, and icon
 */

import React from 'react';

function MetricCard({ title, value, change, isPositive, icon }) {
  return (
    <div className="metric-card">
      <div className="flex items-center justify-between">
        <p className="metric-card-title">{title}</p>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      <p className="metric-card-value">{value}</p>
      {change && (
        <p className={`metric-card-change ${isPositive ? 'positive' : 'negative'}`}>
          <span>{change}</span>
          <span className="ml-1">{isPositive ? '↗' : '↘'}</span>
        </p>
      )}
    </div>
  );
}

export default MetricCard;
