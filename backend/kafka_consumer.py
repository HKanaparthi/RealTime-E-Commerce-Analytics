"""
ShopStream Kafka Consumer

Consumes events from Kafka and writes them to TimescaleDB.
Simple consumer for use without Spark Streaming.

"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict
from kafka import KafkaConsumer
from sqlalchemy import text
from config import settings
from models import get_session, EventRaw
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShopStreamConsumer:
    """Kafka consumer for e-commerce events"""

    def __init__(self):
        """Initialize Kafka consumer"""
        self.consumer = None
        self.session = None
        self.events_processed = 0
        self.batch_size = 100
        self.batch = []

    def connect(self):
        """Connect to Kafka and database"""
        try:
            # Connect to Kafka
            self.consumer = KafkaConsumer(
                settings.KAFKA_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='shopstream-consumer-group',
                max_poll_records=500
            )

            logger.info(f"✅ Connected to Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            logger.info(f"📥 Subscribed to topic: {settings.KAFKA_TOPIC}")

            # Get database session
            self.session = get_session()
            logger.info("✅ Connected to database")

        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            raise

    def process_event(self, event: Dict):
        """Process a single event and add to batch"""
        try:
            # Extract nested product data
            product = event.get('product', {})
            location = event.get('location', {})

            # Create EventRaw object
            event_raw = EventRaw(
                event_id=event['event_id'],
                event_type=event['event_type'],
                timestamp=datetime.fromisoformat(event['timestamp']),
                user_id=event['user_id'],
                session_id=event['session_id'],
                product_id=product.get('id'),
                product_name=product.get('name'),
                product_category=product.get('category'),
                product_price=product.get('price', 0.0),
                quantity=event.get('quantity', 1),
                total_amount=event.get('total_amount', 0.0),
                payment_method=event.get('payment_method'),
                country=location.get('country'),
                city=location.get('city'),
                ip_address=location.get('ip'),
                raw_data=event  # Store full event for reference
            )

            self.batch.append(event_raw)

            # Flush batch if it reaches batch size
            if len(self.batch) >= self.batch_size:
                self.flush_batch()

        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")

    def flush_batch(self):
        """Write batch of events to database"""
        if not self.batch:
            return

        try:
            self.session.bulk_save_objects(self.batch)
            self.session.commit()

            self.events_processed += len(self.batch)

            if self.events_processed % 1000 == 0:
                logger.info(f"📊 Processed {self.events_processed} events")

            self.batch = []

        except Exception as e:
            logger.error(f"❌ Error flushing batch: {e}")
            self.session.rollback()
            self.batch = []

    def aggregate_metrics(self):
        """Aggregate metrics from raw events into metrics tables"""
        try:
            # Get current time
            now = datetime.utcnow()

            # Aggregate 1-minute metrics
            query = text("""
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
                    cart_abandonment_rate
                )
                SELECT
                    date_trunc('minute', timestamp) as time_bucket,
                    COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(COUNT(CASE WHEN event_type = 'purchase' THEN 1 END), 0) as total_orders,
                    CASE
                        WHEN COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) > 0
                        THEN SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END)::float /
                             COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)
                        ELSE 0
                    END as average_order_value,
                    COALESCE(COUNT(CASE WHEN event_type = 'product_view' THEN 1 END), 0) as total_views,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COALESCE(COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END), 0) as add_to_cart_count,
                    COALESCE(COUNT(CASE WHEN event_type = 'remove_from_cart' THEN 1 END), 0) as remove_from_cart_count,
                    COALESCE(COUNT(CASE WHEN event_type = 'purchase' THEN 1 END), 0) as purchase_count,
                    COALESCE(COUNT(CASE WHEN event_type = 'search' THEN 1 END), 0) as search_count,
                    CASE
                        WHEN COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) > 0
                        THEN (COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)::float /
                              COUNT(CASE WHEN event_type = 'product_view' THEN 1 END)) * 100
                        ELSE 0
                    END as conversion_rate,
                    CASE
                        WHEN COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) > 0
                        THEN (1.0 - (COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)::float /
                              COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END))) * 100
                        ELSE 0
                    END as cart_abandonment_rate
                FROM events_raw
                WHERE timestamp >= :start_time
                  AND timestamp < :end_time
                GROUP BY time_bucket
                ON CONFLICT (time_bucket) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_orders = EXCLUDED.total_orders,
                    average_order_value = EXCLUDED.average_order_value,
                    total_views = EXCLUDED.total_views,
                    unique_users = EXCLUDED.unique_users,
                    unique_sessions = EXCLUDED.unique_sessions,
                    add_to_cart_count = EXCLUDED.add_to_cart_count,
                    remove_from_cart_count = EXCLUDED.remove_from_cart_count,
                    purchase_count = EXCLUDED.purchase_count,
                    search_count = EXCLUDED.search_count,
                    conversion_rate = EXCLUDED.conversion_rate,
                    cart_abandonment_rate = EXCLUDED.cart_abandonment_rate
            """)

            # Aggregate last 2 minutes
            start_time = now - timedelta(minutes=2)
            self.session.execute(query, {'start_time': start_time, 'end_time': now})
            self.session.commit()

        except Exception as e:
            logger.error(f"❌ Error aggregating metrics: {e}")
            self.session.rollback()

    def calculate_trending_products(self):
        """Calculate and update trending products based on recent activity"""
        try:
            now = datetime.utcnow()
            time_bucket = now.replace(second=0, microsecond=0)

            # Analyze last 5 minutes for trending calculation
            lookback_start = now - timedelta(minutes=5)

            # Calculate trending products with scores
            query = text("""
                WITH product_stats AS (
                    SELECT
                        product_id,
                        product_name,
                        product_category,
                        product_price,
                        COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) as view_count,
                        COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchase_count,
                        SUM(CASE WHEN event_type = 'purchase' THEN total_amount ELSE 0 END) as revenue
                    FROM events_raw
                    WHERE timestamp >= :lookback_start
                      AND timestamp < :now
                      AND product_id IS NOT NULL
                    GROUP BY product_id, product_name, product_category, product_price
                    HAVING COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) > 0
                ),
                scored_products AS (
                    SELECT
                        product_id,
                        product_name,
                        product_category,
                        product_price,
                        view_count,
                        purchase_count,
                        revenue,
                        view_count::float / 5.0 as views_per_minute,
                        -- Trending score: weighted combination of views, velocity, and conversion
                        (
                            (view_count * 1.0) +                          -- Raw views
                            (view_count::float / 5.0 * 5.0) +            -- Velocity (views/min * 5)
                            (purchase_count * 10.0) +                     -- Purchases worth 10x
                            (CASE WHEN view_count > 0
                             THEN (purchase_count::float / view_count * 100.0)
                             ELSE 0 END)                                  -- Conversion rate %
                        ) as trending_score
                    FROM product_stats
                )
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
                    ROW_NUMBER() OVER (ORDER BY trending_score DESC) as rank
                FROM scored_products
                ORDER BY trending_score DESC
                LIMIT 20
            """)

            results = self.session.execute(
                query,
                {'lookback_start': lookback_start, 'now': now}
            ).fetchall()

            # Clear old trending products for this time bucket
            self.session.execute(
                text("DELETE FROM trending_products WHERE time_bucket = :time_bucket"),
                {'time_bucket': time_bucket}
            )

            # Insert new trending products
            if results:
                insert_query = text("""
                    INSERT INTO trending_products (
                        time_bucket, product_id, product_name, product_category, product_price,
                        view_count, purchase_count, revenue, views_per_minute, trending_score, rank
                    ) VALUES (
                        :time_bucket, :product_id, :product_name, :product_category, :product_price,
                        :view_count, :purchase_count, :revenue, :views_per_minute, :trending_score, :rank
                    )
                """)

                for row in results:
                    self.session.execute(insert_query, {
                        'time_bucket': time_bucket,
                        'product_id': row[0],
                        'product_name': row[1],
                        'product_category': row[2],
                        'product_price': row[3],
                        'view_count': row[4],
                        'purchase_count': row[5],
                        'revenue': row[6],
                        'views_per_minute': row[7],
                        'trending_score': row[8],
                        'rank': row[9]
                    })

                self.session.commit()
                logger.info(f"🔥 Updated {len(results)} trending products")

        except Exception as e:
            logger.error(f"❌ Error calculating trending products: {e}")
            self.session.rollback()

    def run(self):
        """Main consumer loop"""
        self.connect()

        logger.info("🚀 Starting ShopStream consumer...")
        logger.info(f"👨‍💻 Built by {settings.DEVELOPER}")

        last_aggregate = time.time()
        aggregate_interval = 10  # Aggregate every 10 seconds

        try:
            for message in self.consumer:
                event = message.value
                self.process_event(event)

                # Periodically aggregate metrics and calculate trending products
                if time.time() - last_aggregate >= aggregate_interval:
                    self.flush_batch()  # Flush any pending events
                    self.aggregate_metrics()
                    self.calculate_trending_products()
                    last_aggregate = time.time()

        except KeyboardInterrupt:
            logger.info("⏹️  Shutting down consumer...")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
        finally:
            self.flush_batch()  # Flush remaining events
            if self.consumer:
                self.consumer.close()
            if self.session:
                self.session.close()
            logger.info(f"✅ Processed {self.events_processed} total events")


if __name__ == "__main__":
    consumer = ShopStreamConsumer()
    consumer.run()
