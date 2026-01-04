/**
 * TrendingProducts Component
 * Displays top trending products with views per minute
 */

import React from 'react';

function TrendingProducts({ products }) {
  if (!products || products.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No trending products yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {products.slice(0, 10).map((product, index) => (
        <div
          key={product.product_id}
          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <div className="flex items-center space-x-3 flex-1">
            {/* Rank Badge */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              index === 0 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
              index === 1 ? 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300' :
              index === 2 ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300' :
              'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
            }`}>
              {index + 1}
            </div>

            {/* Product Info */}
            <div className="flex-1">
              <p className="font-medium text-gray-900 dark:text-white">
                {product.product_name}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {product.category} • ${product.price?.toFixed(2)}
              </p>
            </div>
          </div>

          {/* Metrics */}
          <div className="text-right">
            <p className="font-semibold text-gray-900 dark:text-white">
              {product.views} views
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {product.views_per_minute?.toFixed(1)} views/min
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default TrendingProducts;
