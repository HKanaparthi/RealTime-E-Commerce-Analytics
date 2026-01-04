"""
ShopStream Kafka Event Producer

Generates realistic e-commerce events and sends them to Kafka.
Simulates user behavior: product views → add to cart → purchase funnel.
"""

import json
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging
from config import settings, get_kafka_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EcommerceEventGenerator:
    """
    Generates realistic e-commerce events with user behavior patterns.
    Simulates a realistic shopping funnel.
    """

    def __init__(self):
        self.products = settings.SAMPLE_PRODUCTS
        self.locations = settings.SAMPLE_LOCATIONS
        self.event_types = settings.EVENT_TYPES
        self.payment_methods = settings.PAYMENT_METHODS

        # Active sessions for realistic user behavior
        self.active_sessions: Dict[str, Dict] = {}
        self.session_timeout = 300  # 5 minutes

    def generate_event(self) -> Dict:
        """
        Generate a single e-commerce event with realistic user behavior.

        Flow:
        1. New users start with product_view
        2. After views, they might add_to_cart (30% chance)
        3. After cart, they might purchase (60% chance) or remove_from_cart (20% chance)
        4. Random searches occur
        """

        # Decide if this is a new session or continuing session
        if random.random() < 0.3 or len(self.active_sessions) == 0:
            # 30% chance of new session
            event = self._create_new_session_event()
        else:
            # Continue existing session
            event = self._continue_session_event()

        # Clean up old sessions (older than 5 minutes)
        self._cleanup_old_sessions()

        return event

    def _create_new_session_event(self) -> Dict:
        """Create event for a new user session (always starts with view or search)"""
        user_id = f"user_{random.randint(1000, 9999)}"
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        product = random.choice(self.products)
        location = random.choice(self.locations)

        # New sessions start with view (80%) or search (20%)
        event_type = random.choice(["product_view"] * 8 + ["search"] * 2)

        # Store session state
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "cart": [],
            "viewed_products": [product["id"]],
            "last_activity": time.time(),
            "location": location,
        }

        if event_type == "search":
            return self._create_search_event(user_id, session_id, location)
        else:
            return self._create_view_event(user_id, session_id, product, location)

    def _continue_session_event(self) -> Dict:
        """Continue an existing user session with realistic behavior"""
        session_id = random.choice(list(self.active_sessions.keys()))
        session = self.active_sessions[session_id]

        user_id = session["user_id"]
        location = session["location"]

        # Update last activity
        session["last_activity"] = time.time()

        # Decide next action based on session state
        if len(session["cart"]) > 0:
            # User has items in cart
            # 60% purchase, 20% remove, 10% view more, 10% abandon (do nothing)
            action = random.choices(
                ["purchase", "remove_from_cart", "product_view", "abandon"],
                weights=[60, 20, 15, 5]
            )[0]

            if action == "purchase":
                return self._create_purchase_event(user_id, session_id, session, location)
            elif action == "remove_from_cart":
                return self._create_remove_from_cart_event(user_id, session_id, session, location)
            elif action == "product_view":
                product = random.choice(self.products)
                session["viewed_products"].append(product["id"])
                return self._create_view_event(user_id, session_id, product, location)
            else:
                # Abandon - create view event
                product = random.choice(self.products)
                return self._create_view_event(user_id, session_id, product, location)

        else:
            # Empty cart - user is browsing
            # 70% view more, 25% add to cart, 5% search
            action = random.choices(
                ["product_view", "add_to_cart", "search"],
                weights=[70, 25, 5]
            )[0]

            if action == "add_to_cart":
                # Add previously viewed product or new one
                if session["viewed_products"]:
                    product = next(
                        (p for p in self.products if p["id"] == random.choice(session["viewed_products"])),
                        random.choice(self.products)
                    )
                else:
                    product = random.choice(self.products)
                return self._create_add_to_cart_event(user_id, session_id, product, session, location)
            elif action == "search":
                return self._create_search_event(user_id, session_id, location)
            else:
                product = random.choice(self.products)
                session["viewed_products"].append(product["id"])
                return self._create_view_event(user_id, session_id, product, location)

    def _create_view_event(self, user_id: str, session_id: str, product: Dict, location: Dict) -> Dict:
        """Create product view event"""
        return {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "event_type": "product_view",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "session_id": session_id,
            "product": {
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"]
            },
            "location": {
                "city": location["city"],
                "country": location["country"],
                "ip": self._generate_fake_ip()
            }
        }

    def _create_add_to_cart_event(self, user_id: str, session_id: str, product: Dict, session: Dict, location: Dict) -> Dict:
        """Create add to cart event"""
        quantity = random.randint(1, 3)

        # Add to session cart
        session["cart"].append({
            "product": product,
            "quantity": quantity
        })

        return {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "event_type": "add_to_cart",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "session_id": session_id,
            "product": {
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"]
            },
            "quantity": quantity,
            "location": {
                "city": location["city"],
                "country": location["country"],
                "ip": self._generate_fake_ip()
            }
        }

    def _create_remove_from_cart_event(self, user_id: str, session_id: str, session: Dict, location: Dict) -> Dict:
        """Create remove from cart event"""
        if not session["cart"]:
            # Fallback if cart is empty
            product = random.choice(self.products)
            return self._create_view_event(user_id, session_id, product, location)

        # Remove random item from cart
        cart_item = random.choice(session["cart"])
        session["cart"].remove(cart_item)
        product = cart_item["product"]

        return {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "event_type": "remove_from_cart",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "session_id": session_id,
            "product": {
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"]
            },
            "quantity": cart_item["quantity"],
            "location": {
                "city": location["city"],
                "country": location["country"],
                "ip": self._generate_fake_ip()
            }
        }

    def _create_purchase_event(self, user_id: str, session_id: str, session: Dict, location: Dict) -> Dict:
        """Create purchase event"""
        if not session["cart"]:
            # Fallback if cart is empty
            product = random.choice(self.products)
            return self._create_view_event(user_id, session_id, product, location)

        # Purchase random item from cart
        cart_item = random.choice(session["cart"])
        session["cart"].remove(cart_item)
        product = cart_item["product"]
        quantity = cart_item["quantity"]
        total_amount = product["price"] * quantity

        return {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "event_type": "purchase",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "session_id": session_id,
            "product": {
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"]
            },
            "quantity": quantity,
            "total_amount": round(total_amount, 2),
            "payment_method": random.choice(self.payment_methods),
            "location": {
                "city": location["city"],
                "country": location["country"],
                "ip": self._generate_fake_ip()
            }
        }

    def _create_search_event(self, user_id: str, session_id: str, location: Dict) -> Dict:
        """Create search event"""
        search_queries = [
            "iphone", "laptop", "headphones", "watch", "camera",
            "nike shoes", "jacket", "coffee maker", "vacuum",
            "gaming console", "smart watch", "wireless earbuds"
        ]

        return {
            "event_id": f"evt_{uuid.uuid4().hex}",
            "event_type": "search",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "session_id": session_id,
            "search_query": random.choice(search_queries),
            "location": {
                "city": location["city"],
                "country": location["country"],
                "ip": self._generate_fake_ip()
            }
        }

    def _generate_fake_ip(self) -> str:
        """Generate a fake IP address"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

    def _cleanup_old_sessions(self):
        """Remove sessions older than timeout"""
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.active_sessions.items()
            if current_time - session["last_activity"] > self.session_timeout
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]


class KafkaEventProducer:
    """
    Kafka producer for sending e-commerce events to Kafka topic.
    Handles connection, retries, and graceful shutdown.
    """

    def __init__(self):
        self.config = get_kafka_config()
        self.producer = None
        self.generator = EcommerceEventGenerator()
        self.connect()

    def connect(self):
        """Connect to Kafka with retry logic"""
        max_retries = 5
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.config["bootstrap_servers"],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',  # Wait for all replicas
                    retries=3,
                    max_in_flight_requests_per_connection=1,  # Ensure ordering
                    compression_type='gzip',
                )
                logger.info(f"✅ Connected to Kafka: {self.config['bootstrap_servers']}")
                return
            except KafkaError as e:
                logger.error(f"❌ Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise

    def send_event(self, event: Dict):
        """Send a single event to Kafka"""
        try:
            future = self.producer.send(self.config["topic"], value=event)
            future.get(timeout=10)  # Block until sent
        except KafkaError as e:
            logger.error(f"❌ Failed to send event: {e}")
            raise

    def start_stream(self, events_per_second: int = 100, duration_seconds: int = None):
        """
        Start generating and sending events at specified rate.

        Args:
            events_per_second: Number of events to generate per second
            duration_seconds: Run for this many seconds (None = infinite)
        """
        logger.info(f"🚀 Starting event stream: {events_per_second} events/sec")
        logger.info(f"📊 Topic: {self.config['topic']}")
        logger.info(f"👨‍💻 Built by Harsha Kanaparthi\n")

        interval = 1.0 / events_per_second
        events_sent = 0
        start_time = time.time()

        try:
            while True:
                event_start = time.time()

                # Generate and send event
                event = self.generator.generate_event()
                self.send_event(event)
                events_sent += 1

                # Log progress every 100 events
                if events_sent % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = events_sent / elapsed
                    logger.info(f"📈 Sent {events_sent} events | Rate: {rate:.1f} events/sec | Active sessions: {len(self.generator.active_sessions)}")

                # Check duration limit
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info(f"⏱️  Duration limit reached ({duration_seconds}s)")
                    break

                # Sleep to maintain rate
                elapsed = time.time() - event_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping event stream (Ctrl+C)")
        finally:
            logger.info(f"📊 Total events sent: {events_sent}")
            self.close()

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("✅ Kafka producer closed")


def main():
    """Main entry point for event generator"""
    import argparse

    parser = argparse.ArgumentParser(description="ShopStream Event Generator by Harsha Kanaparthi")
    parser.add_argument(
        "--rate",
        type=int,
        default=settings.EVENT_RATE,
        help=f"Events per second (default: {settings.EVENT_RATE})"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Run for N seconds (default: infinite)"
    )

    args = parser.parse_args()

    # Validate rate
    if args.rate < settings.EVENT_RATE_MIN or args.rate > settings.EVENT_RATE_MAX:
        logger.error(f"❌ Event rate must be between {settings.EVENT_RATE_MIN} and {settings.EVENT_RATE_MAX}")
        return

    producer = KafkaEventProducer()
    producer.start_stream(events_per_second=args.rate, duration_seconds=args.duration)


if __name__ == "__main__":
    main()
