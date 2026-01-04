"""
ShopStream Database Models
SQLAlchemy models for TimescaleDB hypertables and standard tables.
Supports time-series data for e-commerce analytics.
"""

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, JSON, Boolean,
    Index, Text, create_engine, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import get_database_url

Base = declarative_base()


class EventRaw(Base):
    """
    Raw events table (TimescaleDB hypertable)
    Stores all incoming e-commerce events with full detail
    """
    __tablename__ = "events_raw"

    event_id = Column(String(100), primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)

    # Product information (denormalized for query performance)
    product_id = Column(String(100), index=True)
    product_name = Column(String(255))
    product_category = Column(String(100), index=True)
    product_price = Column(Float)

    # Transaction details
    quantity = Column(Integer, default=1)
    total_amount = Column(Float)
    payment_method = Column(String(50))

    # Location
    city = Column(String(100), index=True)
    country = Column(String(100), index=True)
    ip_address = Column(String(50))

    # Full event data as JSON (for flexibility)
    raw_data = Column(JSON)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_timestamp_event_type', 'timestamp', 'event_type'),
        Index('idx_timestamp_product', 'timestamp', 'product_id'),
        Index('idx_user_session', 'user_id', 'session_id'),
        Index('idx_location', 'country', 'city'),
    )


class Metrics1Min(Base):
    """
    1-minute aggregated metrics (TimescaleDB continuous aggregate)
    Pre-computed metrics for fast dashboard queries
    """
    __tablename__ = "metrics_1min"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_bucket = Column(DateTime, nullable=False, unique=True, index=True)

    # Sales metrics
    total_revenue = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    average_order_value = Column(Float, default=0.0)

    # Traffic metrics
    total_views = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)

    # Funnel metrics
    add_to_cart_count = Column(Integer, default=0)
    remove_from_cart_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)

    # Conversion rates (calculated)
    conversion_rate = Column(Float, default=0.0)  # purchases / views
    cart_abandonment_rate = Column(Float, default=0.0)  # 1 - (purchases / add_to_cart)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class Metrics1Hour(Base):
    """
    1-hour aggregated metrics (TimescaleDB continuous aggregate)
    Longer-term trend analysis
    """
    __tablename__ = "metrics_1hour"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_bucket = Column(DateTime, nullable=False, unique=True, index=True)

    # Sales metrics
    total_revenue = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    average_order_value = Column(Float, default=0.0)

    # Traffic metrics
    total_views = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)

    # Funnel metrics
    add_to_cart_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    cart_abandonment_rate = Column(Float, default=0.0)

    # Peak values
    peak_revenue_per_minute = Column(Float, default=0.0)
    peak_orders_per_minute = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class TrendingProduct(Base):
    """
    Trending products table
    Updated in real-time by Spark streaming job
    """
    __tablename__ = "trending_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_bucket = Column(DateTime, nullable=False, index=True)

    product_id = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_category = Column(String(100))
    product_price = Column(Float)

    # Metrics
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    views_per_minute = Column(Float, default=0.0)

    # Trending score (higher = more trending)
    trending_score = Column(Float, default=0.0)

    # Ranking
    rank = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_time_rank', 'time_bucket', 'rank'),
        Index('idx_trending_score', 'trending_score'),
    )


class Alert(Base):
    """
    System alerts table
    Stores detected anomalies and notifications
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False, index=True)  # spike, drop, low_conversion, etc.
    severity = Column(String(20), default="warning")  # critical, warning, info
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Context
    metric_name = Column(String(100))
    current_value = Column(Float)
    threshold_value = Column(Float)
    percentage_change = Column(Float)

    # Related entities
    product_id = Column(String(100))
    product_name = Column(String(255))

    # Timestamps
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Alert Metadata
    alert_metadata = Column(JSON)

    __table_args__ = (
        Index('idx_active_alerts', 'is_active', 'detected_at'),
        Index('idx_alert_type_time', 'alert_type', 'detected_at'),
    )


class GeographicMetric(Base):
    """
    Geographic sales distribution
    Updated in real-time for map visualizations
    """
    __tablename__ = "geographic_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_bucket = Column(DateTime, nullable=False, index=True)

    country = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False)

    # Metrics
    total_views = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    unique_users = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_geo_time', 'time_bucket', 'country', 'city'),
    )


# Database initialization functions

def get_engine():
    """Create database engine"""
    return create_engine(
        get_database_url(),
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=False  # Set to True for SQL debugging
    )


def get_session():
    """Get database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_database(use_timescale: bool = False):
    """
    Initialize database with tables and optional TimescaleDB extensions.

    Args:
        use_timescale: Enable TimescaleDB features (hypertables, retention policies)
                      Set to False for free tier PostgreSQL (Neon, Supabase, etc.)

    Run this once during deployment.
    """
    engine = get_engine()
    timescale_enabled = False

    # Try to enable TimescaleDB extension if requested
    if use_timescale:
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
                conn.commit()
                timescale_enabled = True
                print("✅ TimescaleDB extension enabled")
            except Exception as e:
                print(f"⚠️  TimescaleDB not available: {e}")
                print("    Falling back to standard PostgreSQL")
                timescale_enabled = False

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # Convert to hypertables (TimescaleDB only)
    if timescale_enabled:
        with engine.connect() as conn:
            try:
                # events_raw hypertable
                conn.execute(text("""
                    SELECT create_hypertable(
                        'events_raw',
                        'timestamp',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    );
                """))

                # metrics_1min hypertable
                conn.execute(text("""
                    SELECT create_hypertable(
                        'metrics_1min',
                        'time_bucket',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    );
                """))

                # metrics_1hour hypertable
                conn.execute(text("""
                    SELECT create_hypertable(
                        'metrics_1hour',
                        'time_bucket',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '7 days'
                    );
                """))

                conn.commit()
                print("✅ TimescaleDB hypertables created")
            except Exception as e:
                print(f"⚠️  Could not create hypertables: {e}")

        # Add data retention policies
        with engine.connect() as conn:
            try:
                # Raw events: 30 days
                conn.execute(text("""
                    SELECT add_retention_policy(
                        'events_raw',
                        INTERVAL '30 days',
                        if_not_exists => TRUE
                    );
                """))

                # 1-min metrics: 7 days
                conn.execute(text("""
                    SELECT add_retention_policy(
                        'metrics_1min',
                        INTERVAL '7 days',
                        if_not_exists => TRUE
                    );
                """))

                # 1-hour metrics: 365 days
                conn.execute(text("""
                    SELECT add_retention_policy(
                        'metrics_1hour',
                        INTERVAL '365 days',
                        if_not_exists => TRUE
                    );
                """))

                conn.commit()
                print("✅ Data retention policies configured")
            except Exception as e:
                print(f"⚠️  Could not set retention policies: {e}")
    else:
        print("ℹ️  Running with standard PostgreSQL (no TimescaleDB features)")
        print("   Consider using Neon.tech or Supabase for free PostgreSQL hosting")

    print(f"🎉 Database initialization complete!")


if __name__ == "__main__":
    print("🗄️  Initializing ShopStream Database...")
    print(f"   Built by Harsha Kanaparthi\n")
    init_database()
