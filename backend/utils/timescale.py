"""
ShopStream TimescaleDB Utilities

Helper functions for TimescaleDB operations, queries, and aggregations.
"""

from datetime import datetime, timedelta
from sqlalchemy import text, func
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TimescaleDBHelper:
    """Helper class for TimescaleDB operations"""

    def __init__(self, session):
        self.session = session

    def get_live_metrics(self, minutes: int = 5) -> Dict:
        """
        Get live metrics for the last N minutes
        Used by the dashboard for real-time display
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)

        query = text("""
            SELECT
                COALESCE(SUM(total_revenue), 0) as revenue,
                COALESCE(SUM(total_orders), 0) as orders,
                COALESCE(AVG(unique_users), 0) as active_users,
                COALESCE(AVG(conversion_rate), 0) as conversion_rate,
                COALESCE(AVG(cart_abandonment_rate), 0) as cart_abandonment_rate
            FROM metrics_1min
            WHERE time_bucket >= :since
        """)

        result = self.session.execute(query, {"since": since}).fetchone()

        if result:
            return {
                "revenue": float(result[0] or 0),
                "orders": int(result[1] or 0),
                "active_users": int(result[2] or 0),
                "conversion_rate": float(result[3] or 0),
                "cart_abandonment_rate": float(result[4] or 0),
            }

        return {
            "revenue": 0,
            "orders": 0,
            "active_users": 0,
            "conversion_rate": 0,
            "cart_abandonment_rate": 0,
        }

    def get_revenue_trend(self, hours: int = 1) -> List[Dict]:
        """
        Get revenue trend over time
        Returns time-series data for charts
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = text("""
            SELECT
                time_bucket,
                total_revenue,
                total_orders,
                average_order_value
            FROM metrics_1min
            WHERE time_bucket >= :since
            ORDER BY time_bucket ASC
        """)

        results = self.session.execute(query, {"since": since}).fetchall()

        return [
            {
                "timestamp": row[0].isoformat(),
                "revenue": float(row[1] or 0),
                "orders": int(row[2] or 0),
                "average_order_value": float(row[3] or 0),
            }
            for row in results
        ]

    def get_trending_products(self, limit: int = 10, minutes: int = 5) -> List[Dict]:
        """
        Get trending products for the last N minutes
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)

        query = text("""
            SELECT
                product_id,
                product_name,
                product_category,
                product_price,
                view_count,
                purchase_count,
                revenue,
                views_per_minute,
                trending_score,
                rank
            FROM trending_products
            WHERE time_bucket >= :since
            ORDER BY rank ASC
            LIMIT :limit
        """)

        results = self.session.execute(
            query, {"since": since, "limit": limit}
        ).fetchall()

        return [
            {
                "product_id": row[0],
                "product_name": row[1],
                "category": row[2],
                "price": float(row[3] or 0),
                "views": int(row[4] or 0),
                "purchases": int(row[5] or 0),
                "revenue": float(row[6] or 0),
                "views_per_minute": float(row[7] or 0),
                "trending_score": float(row[8] or 0),
                "rank": int(row[9] or 0),
            }
            for row in results
        ]

    def get_conversion_funnel(self, hours: int = 1) -> Dict:
        """
        Get conversion funnel metrics (views → cart → purchase)
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = text("""
            SELECT
                SUM(total_views) as views,
                SUM(add_to_cart_count) as add_to_cart,
                SUM(purchase_count) as purchases
            FROM metrics_1min
            WHERE time_bucket >= :since
        """)

        result = self.session.execute(query, {"since": since}).fetchone()

        if result:
            views = int(result[0] or 0)
            cart = int(result[1] or 0)
            purchases = int(result[2] or 0)

            # Calculate rates
            cart_rate = (cart / views * 100) if views > 0 else 0
            purchase_rate = (purchases / views * 100) if views > 0 else 0

            return {
                "views": views,
                "add_to_cart": cart,
                "purchases": purchases,
                "cart_rate": round(cart_rate, 2),
                "conversion_rate": round(purchase_rate, 2),
            }

        return {
            "views": 0,
            "add_to_cart": 0,
            "purchases": 0,
            "cart_rate": 0,
            "conversion_rate": 0,
        }

    def get_geographic_distribution(self, limit: int = 10, hours: int = 1) -> List[Dict]:
        """
        Get geographic sales distribution from raw events
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = text("""
            SELECT
                country,
                city,
                COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END), 0) as revenue,
                COALESCE(COUNT(CASE WHEN event_type = 'purchase' THEN 1 END), 0) as orders,
                COALESCE(COUNT(CASE WHEN event_type = 'product_view' THEN 1 END), 0) as views,
                COUNT(DISTINCT user_id) as users
            FROM events_raw
            WHERE timestamp >= :since
              AND country IS NOT NULL
              AND city IS NOT NULL
            GROUP BY country, city
            ORDER BY revenue DESC
            LIMIT :limit
        """)

        results = self.session.execute(
            query, {"since": since, "limit": limit}
        ).fetchall()

        return [
            {
                "country": row[0],
                "city": row[1],
                "revenue": float(row[2] or 0),
                "orders": int(row[3] or 0),
                "views": int(row[4] or 0),
                "users": int(row[5] or 0),
            }
            for row in results
        ]

    def get_active_alerts(self, limit: int = 10) -> List[Dict]:
        """
        Get active alerts (not resolved)
        """
        query = text("""
            SELECT
                id,
                alert_type,
                severity,
                title,
                description,
                metric_name,
                current_value,
                threshold_value,
                percentage_change,
                product_name,
                detected_at
            FROM alerts
            WHERE is_active = TRUE
            ORDER BY detected_at DESC
            LIMIT :limit
        """)

        results = self.session.execute(query, {"limit": limit}).fetchall()

        return [
            {
                "id": row[0],
                "type": row[1],
                "severity": row[2],
                "title": row[3],
                "description": row[4],
                "metric": row[5],
                "current_value": float(row[6] or 0),
                "threshold": float(row[7] or 0),
                "change_percent": float(row[8] or 0),
                "product": row[9],
                "detected_at": row[10].isoformat() if row[10] else None,
            }
            for row in results
        ]

    def get_hourly_comparison(self) -> Dict:
        """
        Compare current hour vs previous hour
        Returns percentage changes for key metrics
        """
        current_hour_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        previous_hour_start = current_hour_start - timedelta(hours=1)

        query = text("""
            WITH current_hour AS (
                SELECT
                    SUM(total_revenue) as revenue,
                    SUM(total_orders) as orders,
                    AVG(conversion_rate) as conversion
                FROM metrics_1min
                WHERE time_bucket >= :current_hour
            ),
            previous_hour AS (
                SELECT
                    SUM(total_revenue) as revenue,
                    SUM(total_orders) as orders,
                    AVG(conversion_rate) as conversion
                FROM metrics_1min
                WHERE time_bucket >= :previous_hour
                AND time_bucket < :current_hour
            )
            SELECT
                c.revenue as curr_revenue,
                c.orders as curr_orders,
                c.conversion as curr_conversion,
                p.revenue as prev_revenue,
                p.orders as prev_orders,
                p.conversion as prev_conversion
            FROM current_hour c, previous_hour p
        """)

        result = self.session.execute(
            query,
            {
                "current_hour": current_hour_start,
                "previous_hour": previous_hour_start,
            }
        ).fetchone()

        if result:
            curr_revenue = float(result[0] or 0)
            prev_revenue = float(result[3] or 0)
            curr_orders = int(result[1] or 0)
            prev_orders = int(result[4] or 0)

            revenue_change = (
                ((curr_revenue - prev_revenue) / prev_revenue * 100)
                if prev_revenue > 0 else 0
            )
            orders_change = (
                ((curr_orders - prev_orders) / prev_orders * 100)
                if prev_orders > 0 else 0
            )

            return {
                "revenue_change_percent": round(revenue_change, 1),
                "orders_change_percent": round(orders_change, 1),
                "current_revenue": curr_revenue,
                "current_orders": curr_orders,
            }

        return {
            "revenue_change_percent": 0,
            "orders_change_percent": 0,
            "current_revenue": 0,
            "current_orders": 0,
        }


def test_timescale_queries():
    """Test TimescaleDB queries"""
    from models import get_session

    session = get_session()
    helper = TimescaleDBHelper(session)

    print("🧪 Testing TimescaleDB Queries\n")

    print("📊 Live Metrics:")
    print(helper.get_live_metrics(minutes=5))

    print("\n📈 Revenue Trend (Last Hour):")
    print(helper.get_revenue_trend(hours=1))

    print("\n🔥 Trending Products:")
    print(helper.get_trending_products(limit=5))

    print("\n📉 Conversion Funnel:")
    print(helper.get_conversion_funnel(hours=1))

    print("\n🌍 Geographic Distribution:")
    print(helper.get_geographic_distribution(limit=5))

    print("\n⚠️  Active Alerts:")
    print(helper.get_active_alerts(limit=5))

    print("\n⏰ Hourly Comparison:")
    print(helper.get_hourly_comparison())

    session.close()


if __name__ == "__main__":
    test_timescale_queries()
