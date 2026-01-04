"""
ShopStream Simple Event Generator 

Generates realistic e-commerce events and writes directly to PostgreSQL.
Replaces Kafka + Spark with direct database writes for free tier deployment.
"""

import time
import asyncio
from datetime import datetime
from typing import Dict
import logging
from sqlalchemy import text
from models import get_session, EventRaw
from config import settings
from kafka_producer import EcommerceEventGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleEventProcessor:
    """
    Simplified event processor that writes directly to PostgreSQL.
    Performs real-time aggregation using database queries.
    """

    def __init__(self):
        self.generator = EcommerceEventGenerator()
        self.session = get_session()

    def process_event(self, event: Dict):
        """Process a single event and write to database"""
        try:
            # Create raw event record
            raw_event = EventRaw(
                event_id=event['event_id'],
                event_type=event['event_type'],
                timestamp=datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')),
                user_id=event['user_id'],
                session_id=event['session_id'],
                product_id=event.get('product', {}).get('id'),
                product_name=event.get('product', {}).get('name'),
                product_category=event.get('product', {}).get('category'),
                product_price=event.get('product', {}).get('price'),
                quantity=event.get('quantity', 1),
                total_amount=event.get('total_amount'),
                payment_method=event.get('payment_method'),
                city=event.get('location', {}).get('city'),
                country=event.get('location', {}).get('country'),
                ip_address=event.get('location', {}).get('ip'),
                raw_data=event
            )

            self.session.add(raw_event)
            self.session.commit()

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            self.session.rollback()

    def update_aggregates(self):
        """
        Update aggregate metrics tables.
        Runs periodically to compute 1-minute metrics.
        """
        try:
            # Delete old 1-minute metrics (keep last 7 days)
            self.session.execute(text("""
                DELETE FROM metrics_1min
                WHERE time_bucket < NOW() - INTERVAL '7 days'
            """))

            # Compute 1-minute metrics from raw events
            self.session.execute(text("""
                INSERT INTO metrics_1min (
                    time_bucket,
                    total_revenue,
                    total_orders,
                    average_order_value,
                    total_views,
                    unique_users,
                    unique_sessions,
                    add_to_cart_count,
                    remove_from_cart_count,
                    purchase_count,
                    search_count,
                    conversion_rate,
                    cart_abandonment_rate,
                    created_at
                )
                SELECT
                    date_trunc('minute', timestamp) as time_bucket,
                    COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END), 0) as total_revenue,
                    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as total_orders,
                    AVG(CASE WHEN event_type = 'purchase' THEN total_amount END) as average_order_value,
                    COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) as total_views,
                    COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN user_id END) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) as add_to_cart_count,
                    COUNT(CASE WHEN event_type = 'remove_from_cart' THEN 1 END) as remove_from_cart_count,
                    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchase_count,
                    COUNT(CASE WHEN event_type = 'search' THEN 1 END) as search_count,
                    CASE
                        WHEN COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) > 0
                        THEN (COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)::float /
                              COUNT(CASE WHEN event_type = 'product_view' THEN 1 END)) * 100
                        ELSE 0
                    END as conversion_rate,
                    CASE
                        WHEN COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) > 0
                        THEN (1 - COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)::float /
                              COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END)) * 100
                        ELSE 0
                    END as cart_abandonment_rate,
                    NOW() as created_at
                FROM events_raw
                WHERE timestamp >= date_trunc('minute', NOW() - INTERVAL '2 minutes')
                  AND timestamp < date_trunc('minute', NOW())
                  AND NOT EXISTS (
                      SELECT 1 FROM metrics_1min m
                      WHERE m.time_bucket = date_trunc('minute', events_raw.timestamp)
                  )
                GROUP BY date_trunc('minute', timestamp)
                ON CONFLICT (time_bucket) DO NOTHING
            """))

            # Update trending products
            self.session.execute(text("""
                DELETE FROM trending_products
                WHERE time_bucket < NOW() - INTERVAL '1 hour'
            """))

            self.session.execute(text("""
                INSERT INTO trending_products (
                    time_bucket,
                    product_id,
                    product_name,
                    product_category,
                    product_price,
                    view_count,
                    purchase_count,
                    revenue,
                    views_per_minute,
                    trending_score,
                    updated_at
                )
                SELECT
                    date_trunc('minute', timestamp) as time_bucket,
                    product_id,
                    MAX(product_name) as product_name,
                    MAX(product_category) as product_category,
                    MAX(product_price) as product_price,
                    COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) as view_count,
                    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchase_count,
                    COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END), 0) as revenue,
                    COUNT(CASE WHEN event_type = 'product_view' THEN 1 END)::float as views_per_minute,
                    (COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) * 10 +
                     COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) * 50) as trending_score,
                    NOW() as updated_at
                FROM events_raw
                WHERE timestamp >= NOW() - INTERVAL '5 minutes'
                  AND product_id IS NOT NULL
                GROUP BY date_trunc('minute', timestamp), product_id
                ON CONFLICT DO NOTHING
            """))

            # Update geographic metrics
            self.session.execute(text("""
                DELETE FROM geographic_metrics
                WHERE time_bucket < NOW() - INTERVAL '1 hour'
            """))

            self.session.execute(text("""
                INSERT INTO geographic_metrics (
                    time_bucket,
                    country,
                    city,
                    total_views,
                    total_orders,
                    total_revenue,
                    unique_users,
                    updated_at
                )
                SELECT
                    date_trunc('minute', timestamp) as time_bucket,
                    country,
                    city,
                    COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) as total_views,
                    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as total_orders,
                    COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END), 0) as total_revenue,
                    COUNT(DISTINCT user_id) as unique_users,
                    NOW() as updated_at
                FROM events_raw
                WHERE timestamp >= NOW() - INTERVAL '5 minutes'
                  AND country IS NOT NULL
                GROUP BY date_trunc('minute', timestamp), country, city
                ON CONFLICT DO NOTHING
            """))

            self.session.commit()
            logger.debug("✅ Aggregates updated")

        except Exception as e:
            logger.error(f"Error updating aggregates: {e}")
            self.session.rollback()

    def start_stream(self, events_per_second: int = 10, update_interval: int = 60):
        """
        Start generating and processing events.

        Args:
            events_per_second: Number of events to generate per second (lower for free tier)
            update_interval: How often to update aggregates in seconds
        """
        logger.info(f"🚀 Starting simplified event stream: {events_per_second} events/sec")
        logger.info(f"📊 Writing directly to PostgreSQL")
        logger.info(f"👨‍💻 Built by Harsha Kanaparthi\n")

        interval = 1.0 / events_per_second
        events_sent = 0
        start_time = time.time()
        last_aggregate_update = time.time()

        try:
            while True:
                event_start = time.time()

                # Generate and process event
                event = self.generator.generate_event()
                self.process_event(event)
                events_sent += 1

                # Log progress every 100 events
                if events_sent % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = events_sent / elapsed
                    logger.info(f"📈 Processed {events_sent} events | Rate: {rate:.1f} events/sec | Active sessions: {len(self.generator.active_sessions)}")

                # Update aggregates periodically
                if time.time() - last_aggregate_update >= update_interval:
                    logger.info("🔄 Updating aggregates...")
                    self.update_aggregates()
                    last_aggregate_update = time.time()

                # Sleep to maintain rate
                elapsed = time.time() - event_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping event stream (Ctrl+C)")
        finally:
            logger.info(f"📊 Total events processed: {events_sent}")
            self.session.close()

    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
            logger.info("✅ Database session closed")


def main():
    """Main entry point for simplified event generator"""
    import argparse

    parser = argparse.ArgumentParser(description="ShopStream Simple Event Generator (Free Tier)")
    parser.add_argument(
        "--rate",
        type=int,
        default=10,
        help="Events per second (default: 10 for free tier)"
    )
    parser.add_argument(
        "--update-interval",
        type=int,
        default=60,
        help="Aggregate update interval in seconds (default: 60)"
    )

    args = parser.parse_args()

    # Validate rate (lower limits for free tier)
    if args.rate < 1 or args.rate > 100:
        logger.error("❌ Event rate must be between 1 and 100 for free tier")
        return

    processor = SimpleEventProcessor()
    processor.start_stream(events_per_second=args.rate, update_interval=args.update_interval)


if __name__ == "__main__":
    main()
