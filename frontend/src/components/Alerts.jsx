/**
 * Alerts Component
 * Displays active system alerts and notifications
 */

import React from 'react';

function Alerts({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-3">
          <span className="text-3xl">✅</span>
        </div>
        <p className="text-gray-600 dark:text-gray-400 font-medium">
          All systems normal
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
          No alerts detected
        </p>
      </div>
    );
  }

  // Get severity color classes
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'info':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  // Get severity icon
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '•';
    }
  };

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {alerts.map((alert, index) => (
        <div
          key={alert.id || index}
          className={`border-l-4 p-4 rounded-r-lg ${getSeverityColor(alert.severity)}`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <span className="text-lg">{getSeverityIcon(alert.severity)}</span>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  {alert.title}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {alert.description}
                </p>
                {alert.change_percent !== undefined && alert.change_percent !== 0 && (
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                    Change: {alert.change_percent > 0 ? '+' : ''}{alert.change_percent.toFixed(1)}%
                  </p>
                )}
              </div>
            </div>
            <span className={`alert-badge ${alert.severity}`}>
              {alert.severity}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default Alerts;
