"""
ShopStream Alert Detection Syste

Detects anomalies and generates alerts based on metric thresholds.
Monitors traffic spikes, drops, conversion rates, and trending products.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import text
import logging
from config import settings

logger = logging.getLogger(__name__)


class AlertDetector:
    """
    Detects anomalies in real-time metrics and creates alerts.
    Runs periodically to monitor key metrics.
    """

    def __init__(self, session):
        self.session = session

    def detect_traffic_spike(self, minutes: int = 5) -> Optional[Dict]:
        """
        Detect sudden traffic spikes (>50% increase).
        Compares current period vs previous period.
        """
        current_time = datetime.utcnow()
        current_start = current_time - timedelta(minutes=minutes)
        previous_start = current_start - timedelta(minutes=minutes)

        query = text("""
            WITH current_period AS (
                SELECT SUM(total_views) as views
                FROM metrics_1min
                WHERE time_bucket >= :current_start
            ),
            previous_period AS (
                SELECT SUM(total_views) as views
                FROM metrics_1min
                WHERE time_bucket >= :previous_start
                AND time_bucket < :current_start
            )
            SELECT
                c.views as current_views,
                p.views as previous_views,
                ((c.views - p.views)::float / NULLIF(p.views, 0) * 100) as change_percent
            FROM current_period c, previous_period p
        """)

        result = self.session.execute(
            query,
            {
                "current_start": current_start,
                "previous_start": previous_start,
            }
        ).fetchone()

        if result:
            current_views = result[0] or 0
            previous_views = result[1] or 0
            change_percent = result[2] or 0

            if change_percent > (settings.TRAFFIC_SPIKE_THRESHOLD * 100):
                return {
                    "alert_type": "traffic_spike",
                    "severity": "warning",
                    "title": f"Traffic Spike Detected (+{change_percent:.0f}%)",
                    "description": f"Traffic increased from {previous_views} to {current_views} views in the last {minutes} minutes.",
                    "metric_name": "total_views",
                    "current_value": current_views,
                    "threshold_value": previous_views,
                    "percentage_change": change_percent,
                }

        return None

    def detect_traffic_drop(self, minutes: int = 5) -> Optional[Dict]:
        """
        Detect sudden traffic drops (>30% decrease).
        """
        current_time = datetime.utcnow()
        current_start = current_time - timedelta(minutes=minutes)
        previous_start = current_start - timedelta(minutes=minutes)

        query = text("""
            WITH current_period AS (
                SELECT SUM(total_views) as views
                FROM metrics_1min
                WHERE time_bucket >= :current_start
            ),
            previous_period AS (
                SELECT SUM(total_views) as views
                FROM metrics_1min
                WHERE time_bucket >= :previous_start
                AND time_bucket < :current_start
            )
            SELECT
                c.views as current_views,
                p.views as previous_views,
                ((p.views - c.views)::float / NULLIF(p.views, 0) * 100) as drop_percent
            FROM current_period c, previous_period p
        """)

        result = self.session.execute(
            query,
            {
                "current_start": current_start,
                "previous_start": previous_start,
            }
        ).fetchone()

        if result:
            current_views = result[0] or 0
            previous_views = result[1] or 0
            drop_percent = result[2] or 0

            if drop_percent > (settings.TRAFFIC_DROP_THRESHOLD * 100):
                return {
                    "alert_type": "traffic_drop",
                    "severity": "critical",
                    "title": f"Traffic Drop Detected (-{drop_percent:.0f}%)",
                    "description": f"Traffic decreased from {previous_views} to {current_views} views in the last {minutes} minutes.",
                    "metric_name": "total_views",
                    "current_value": current_views,
                    "threshold_value": previous_views,
                    "percentage_change": -drop_percent,
                }

        return None

    def detect_low_conversion_rate(self, minutes: int = 10) -> Optional[Dict]:
        """
        Detect abnormally low conversion rates (<3%).
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)

        query = text("""
            SELECT
                AVG(conversion_rate) as avg_conversion_rate,
                SUM(total_views) as total_views,
                SUM(purchase_count) as total_purchases
            FROM metrics_1min
            WHERE time_bucket >= :since
        """)

        result = self.session.execute(query, {"since": since}).fetchone()

        if result:
            avg_conversion = result[0] or 0
            total_views = result[1] or 0
            total_purchases = result[2] or 0

            if avg_conversion < (settings.LOW_CONVERSION_THRESHOLD * 100) and total_views > 100:
                return {
                    "alert_type": "low_conversion",
                    "severity": "warning",
                    "title": f"Low Conversion Rate ({avg_conversion:.1f}%)",
                    "description": f"Conversion rate dropped to {avg_conversion:.1f}% ({total_purchases} purchases / {total_views} views).",
                    "metric_name": "conversion_rate",
                    "current_value": avg_conversion,
                    "threshold_value": settings.LOW_CONVERSION_THRESHOLD * 100,
                    "percentage_change": 0,
                }

        return None

    def detect_high_cart_abandonment(self, minutes: int = 10) -> Optional[Dict]:
        """
        Detect high cart abandonment rates (>80%).
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)

        query = text("""
            SELECT
                AVG(cart_abandonment_rate) as avg_abandonment_rate,
                SUM(add_to_cart_count) as total_cart_adds,
                SUM(purchase_count) as total_purchases
            FROM metrics_1min
            WHERE time_bucket >= :since
            AND add_to_cart_count > 0
        """)

        result = self.session.execute(query, {"since": since}).fetchone()

        if result:
            avg_abandonment = result[0] or 0
            total_cart_adds = result[1] or 0
            total_purchases = result[2] or 0

            if avg_abandonment > (settings.HIGH_ABANDONMENT_THRESHOLD * 100) and total_cart_adds > 10:
                return {
                    "alert_type": "high_cart_abandonment",
                    "severity": "warning",
                    "title": f"High Cart Abandonment ({avg_abandonment:.0f}%)",
                    "description": f"Cart abandonment rate is {avg_abandonment:.0f}% ({total_cart_adds} adds, {total_purchases} purchases).",
                    "metric_name": "cart_abandonment_rate",
                    "current_value": avg_abandonment,
                    "threshold_value": settings.HIGH_ABANDONMENT_THRESHOLD * 100,
                    "percentage_change": 0,
                }

        return None

    def detect_trending_products(self, minutes: int = 5) -> List[Dict]:
        """
        Detect products with abnormally high view rates (3x+ normal).
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)

        query = text("""
            SELECT
                product_id,
                product_name,
                views_per_minute,
                view_count
            FROM trending_products
            WHERE time_bucket >= :since
            AND views_per_minute > :threshold
            ORDER BY views_per_minute DESC
            LIMIT 5
        """)

        # Calculate threshold (3x average)
        avg_query = text("""
            SELECT AVG(views_per_minute) as avg_views
            FROM trending_products
            WHERE time_bucket >= :since
        """)

        avg_result = self.session.execute(avg_query, {"since": since}).fetchone()
        avg_views = (avg_result[0] or 10) if avg_result else 10
        threshold = avg_views * settings.TRENDING_MULTIPLIER

        results = self.session.execute(
            query,
            {"since": since, "threshold": threshold}
        ).fetchall()

        alerts = []
        for row in results:
            product_id = row[0]
            product_name = row[1]
            views_per_min = row[2]
            view_count = row[3]

            alerts.append({
                "alert_type": "trending_product",
                "severity": "info",
                "title": f"Trending: {product_name}",
                "description": f"{product_name} is trending with {views_per_min:.0f} views/min ({view_count} total views).",
                "metric_name": "views_per_minute",
                "current_value": views_per_min,
                "threshold_value": threshold,
                "percentage_change": ((views_per_min - avg_views) / avg_views * 100),
                "product_id": product_id,
                "product_name": product_name,
            })

        return alerts

    def detect_revenue_anomaly(self, minutes: int = 10) -> Optional[Dict]:
        """
        Detect unusual revenue patterns (very high or very low).
        """
        current_time = datetime.utcnow()
        current_start = current_time - timedelta(minutes=minutes)
        previous_start = current_start - timedelta(minutes=minutes)

        query = text("""
            WITH current_period AS (
                SELECT SUM(total_revenue) as revenue
                FROM metrics_1min
                WHERE time_bucket >= :current_start
            ),
            previous_period AS (
                SELECT SUM(total_revenue) as revenue
                FROM metrics_1min
                WHERE time_bucket >= :previous_start
                AND time_bucket < :current_start
            )
            SELECT
                c.revenue as current_revenue,
                p.revenue as previous_revenue,
                ((c.revenue - p.revenue)::float / NULLIF(p.revenue, 0) * 100) as change_percent
            FROM current_period c, previous_period p
        """)

        result = self.session.execute(
            query,
            {
                "current_start": current_start,
                "previous_start": previous_start,
            }
        ).fetchone()

        if result:
            current_revenue = result[0] or 0
            previous_revenue = result[1] or 0
            change_percent = result[2] or 0

            # Alert on significant changes (>100% increase or >50% decrease)
            if abs(change_percent) > 100 and previous_revenue > 0:
                severity = "warning" if change_percent > 0 else "critical"
                direction = "increased" if change_percent > 0 else "decreased"

                return {
                    "alert_type": "revenue_anomaly",
                    "severity": severity,
                    "title": f"Revenue Anomaly Detected ({change_percent:+.0f}%)",
                    "description": f"Revenue {direction} from ${previous_revenue:.2f} to ${current_revenue:.2f}.",
                    "metric_name": "total_revenue",
                    "current_value": current_revenue,
                    "threshold_value": previous_revenue,
                    "percentage_change": change_percent,
                }

        return None

    def create_alert(self, alert_data: Dict) -> int:
        """
        Create a new alert in the database.
        Returns alert ID.
        """
        insert_query = text("""
            INSERT INTO alerts (
                alert_type, severity, title, description,
                metric_name, current_value, threshold_value, percentage_change,
                product_id, product_name, detected_at, is_active
            ) VALUES (
                :alert_type, :severity, :title, :description,
                :metric_name, :current_value, :threshold_value, :percentage_change,
                :product_id, :product_name, NOW(), TRUE
            )
            RETURNING id
        """)

        result = self.session.execute(
            insert_query,
            {
                "alert_type": alert_data.get("alert_type"),
                "severity": alert_data.get("severity", "info"),
                "title": alert_data.get("title"),
                "description": alert_data.get("description"),
                "metric_name": alert_data.get("metric_name"),
                "current_value": alert_data.get("current_value"),
                "threshold_value": alert_data.get("threshold_value"),
                "percentage_change": alert_data.get("percentage_change"),
                "product_id": alert_data.get("product_id"),
                "product_name": alert_data.get("product_name"),
            }
        )

        self.session.commit()
        alert_id = result.fetchone()[0]
        logger.info(f"⚠️  Alert created: {alert_data.get('title')} (ID: {alert_id})")
        return alert_id

    def auto_resolve_old_alerts(self, hours: int = 1):
        """
        Auto-resolve alerts older than N hours.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        update_query = text("""
            UPDATE alerts
            SET is_active = FALSE, resolved_at = NOW()
            WHERE is_active = TRUE
            AND detected_at < :cutoff
        """)

        result = self.session.execute(update_query, {"cutoff": cutoff})
        self.session.commit()

        if result.rowcount > 0:
            logger.info(f"✅ Auto-resolved {result.rowcount} old alerts")

    def run_all_checks(self):
        """
        Run all alert detection checks and create alerts if needed.
        Call this periodically (e.g., every 1 minute).
        """
        logger.info("🔍 Running alert detection checks...")

        alerts_created = 0

        # 1. Traffic spike
        alert = self.detect_traffic_spike(minutes=5)
        if alert:
            self.create_alert(alert)
            alerts_created += 1

        # 2. Traffic drop
        alert = self.detect_traffic_drop(minutes=5)
        if alert:
            self.create_alert(alert)
            alerts_created += 1

        # 3. Low conversion rate
        alert = self.detect_low_conversion_rate(minutes=10)
        if alert:
            self.create_alert(alert)
            alerts_created += 1

        # 4. High cart abandonment
        alert = self.detect_high_cart_abandonment(minutes=10)
        if alert:
            self.create_alert(alert)
            alerts_created += 1

        # 5. Trending products
        trending_alerts = self.detect_trending_products(minutes=5)
        for alert in trending_alerts:
            self.create_alert(alert)
            alerts_created += 1

        # 6. Revenue anomaly
        alert = self.detect_revenue_anomaly(minutes=10)
        if alert:
            self.create_alert(alert)
            alerts_created += 1

        # 7. Auto-resolve old alerts
        self.auto_resolve_old_alerts(hours=1)

        if alerts_created > 0:
            logger.info(f"🚨 Created {alerts_created} new alerts")
        else:
            logger.debug("✅ No alerts detected")

        return alerts_created


def test_alert_detection():
    """Test alert detection system"""
    from models import get_session

    session = get_session()
    detector = AlertDetector(session)

    print("🧪 Testing Alert Detection\n")

    print("🔍 Running all checks...")
    alerts_created = detector.run_all_checks()
    print(f"✅ Created {alerts_created} alerts\n")

    session.close()


if __name__ == "__main__":
    test_alert_detection()
