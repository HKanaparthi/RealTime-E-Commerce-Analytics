/**
 * ConversionFunnel Component
 * Visualizes the conversion funnel: Views → Cart → Purchase
 */

import React from 'react';

function ConversionFunnel({ data }) {
  const {
    views = 0,
    add_to_cart = 0,
    purchases = 0,
    conversion_rate = 0,
  } = data;

  // Calculate percentages for visual bars
  const maxValue = Math.max(views, add_to_cart, purchases) || 1;
  const viewsPercent = (views / maxValue) * 100;
  const cartPercent = (add_to_cart / maxValue) * 100;
  const purchasesPercent = (purchases / maxValue) * 100;

  return (
    <div className="space-y-6">
      {/* Funnel Stages */}
      <div className="space-y-4">
        {/* Views */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              👁️ Product Views
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {views.toLocaleString()}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${viewsPercent}%` }}
            />
          </div>
        </div>

        {/* Add to Cart */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              🛒 Add to Cart
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {add_to_cart.toLocaleString()}
              {views > 0 && (
                <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                  ({((add_to_cart / views) * 100).toFixed(1)}%)
                </span>
              )}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-yellow-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${cartPercent}%` }}
            />
          </div>
        </div>

        {/* Purchases */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              ✅ Purchases
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {purchases.toLocaleString()}
              {views > 0 && (
                <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                  ({((purchases / views) * 100).toFixed(1)}%)
                </span>
              )}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-green-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${purchasesPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Conversion Rate Summary */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Overall Conversion Rate
          </span>
          <span className={`text-lg font-bold ${
            conversion_rate >= 7 ? 'text-green-600 dark:text-green-400' :
            conversion_rate >= 3 ? 'text-yellow-600 dark:text-yellow-400' :
            'text-red-600 dark:text-red-400'
          }`}>
            {conversion_rate.toFixed(1)}%
          </span>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {purchases.toLocaleString()} purchases from {views.toLocaleString()} views
        </p>
      </div>
    </div>
  );
}

export default ConversionFunnel;
