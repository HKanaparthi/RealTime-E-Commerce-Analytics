"""
ShopStream Configuration

Centralized configuration for Kafka, Spark, TimescaleDB, and API settings.
Supports both local (Docker) and cloud (Railway) deployments.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "ShopStream"
    APP_VERSION: str = "1.0.0"
    DEVELOPER: str = "Harsha Kanaparthi"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ]

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )
    KAFKA_TOPIC: str = "ecommerce-events"
    KAFKA_CONSUMER_GROUP: str = "shopstream-processors"
    KAFKA_PARTITIONS: int = 3
    KAFKA_REPLICATION_FACTOR: int = 1

    # Spark Configuration
    SPARK_APP_NAME: str = "ShopStream-Processor"
    SPARK_MASTER: str = os.getenv("SPARK_MASTER", "local[*]")
    SPARK_CHECKPOINT_DIR: str = os.getenv(
        "SPARK_CHECKPOINT_DIR",
        "/tmp/shopstream-checkpoints"
    )

    # TimescaleDB/PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/shopstream"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Event Generator
    EVENT_RATE: int = int(os.getenv("EVENT_RATE", "100"))  # events per second
    EVENT_RATE_MIN: int = 10
    EVENT_RATE_MAX: int = 1000

    # Windowing
    WINDOW_1MIN: str = "1 minute"
    WINDOW_5MIN: str = "5 minutes"
    WINDOW_1HOUR: str = "1 hour"

    # Alerts
    TRAFFIC_SPIKE_THRESHOLD: float = 0.50  # 50% increase
    TRAFFIC_DROP_THRESHOLD: float = 0.30   # 30% decrease
    LOW_CONVERSION_THRESHOLD: float = 0.03  # 3%
    HIGH_ABANDONMENT_THRESHOLD: float = 0.80  # 80%
    TRENDING_MULTIPLIER: float = 3.0  # 3x normal views

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_UPDATE_INTERVAL: int = 1  # seconds

    # Data Retention
    RAW_DATA_RETENTION_DAYS: int = 30
    AGGREGATED_DATA_RETENTION_DAYS: int = 365

    # Sample Products (Realistic E-Commerce Catalog)
    SAMPLE_PRODUCTS: list = [
        # Electronics
        {"id": "prod_001", "name": "iPhone 15 Pro", "category": "Electronics", "price": 999.00},
        {"id": "prod_002", "name": "MacBook Pro 16\"", "category": "Electronics", "price": 2499.00},
        {"id": "prod_003", "name": "AirPods Pro", "category": "Electronics", "price": 249.00},
        {"id": "prod_004", "name": "iPad Air", "category": "Electronics", "price": 599.00},
        {"id": "prod_005", "name": "Apple Watch Series 9", "category": "Electronics", "price": 399.00},
        {"id": "prod_006", "name": "Samsung Galaxy S24", "category": "Electronics", "price": 899.00},
        {"id": "prod_007", "name": "Sony WH-1000XM5", "category": "Electronics", "price": 399.00},
        {"id": "prod_008", "name": "Dell XPS 15", "category": "Electronics", "price": 1799.00},
        {"id": "prod_009", "name": "Nintendo Switch OLED", "category": "Electronics", "price": 349.00},
        {"id": "prod_010", "name": "GoPro HERO 12", "category": "Electronics", "price": 499.00},

        # Fashion
        {"id": "prod_011", "name": "Nike Air Max", "category": "Fashion", "price": 149.00},
        {"id": "prod_012", "name": "Levi's 501 Jeans", "category": "Fashion", "price": 79.00},
        {"id": "prod_013", "name": "Ray-Ban Aviators", "category": "Fashion", "price": 159.00},
        {"id": "prod_014", "name": "North Face Jacket", "category": "Fashion", "price": 299.00},
        {"id": "prod_015", "name": "Adidas Ultraboost", "category": "Fashion", "price": 189.00},

        # Home & Kitchen
        {"id": "prod_016", "name": "Dyson V15 Vacuum", "category": "Home", "price": 649.00},
        {"id": "prod_017", "name": "Nespresso Machine", "category": "Home", "price": 199.00},
        {"id": "prod_018", "name": "KitchenAid Mixer", "category": "Home", "price": 449.00},
        {"id": "prod_019", "name": "iRobot Roomba", "category": "Home", "price": 599.00},
        {"id": "prod_020", "name": "Instant Pot Duo", "category": "Home", "price": 99.00},

        # Books & Media
        {"id": "prod_021", "name": "Kindle Paperwhite", "category": "Books", "price": 139.00},
        {"id": "prod_022", "name": "AirPods Max", "category": "Electronics", "price": 549.00},
        {"id": "prod_023", "name": "Bose SoundLink", "category": "Electronics", "price": 129.00},

        # Sports & Outdoors
        {"id": "prod_024", "name": "Yoga Mat Premium", "category": "Sports", "price": 49.00},
        {"id": "prod_025", "name": "Hydro Flask 32oz", "category": "Sports", "price": 44.00},
        {"id": "prod_026", "name": "Fitbit Charge 6", "category": "Electronics", "price": 159.00},
        {"id": "prod_027", "name": "Camping Tent 4P", "category": "Sports", "price": 249.00},

        # Gaming
        {"id": "prod_028", "name": "PlayStation 5", "category": "Electronics", "price": 499.00},
        {"id": "prod_029", "name": "Xbox Series X", "category": "Electronics", "price": 499.00},
        {"id": "prod_030", "name": "Gaming Headset", "category": "Electronics", "price": 89.00},
    ]

    # Geographic Locations (for realistic event data)
    SAMPLE_LOCATIONS: list = [
        {"city": "New York", "country": "USA"},
        {"city": "Los Angeles", "country": "USA"},
        {"city": "Chicago", "country": "USA"},
        {"city": "San Francisco", "country": "USA"},
        {"city": "Seattle", "country": "USA"},
        {"city": "London", "country": "UK"},
        {"city": "Paris", "country": "France"},
        {"city": "Berlin", "country": "Germany"},
        {"city": "Tokyo", "country": "Japan"},
        {"city": "Sydney", "country": "Australia"},
        {"city": "Toronto", "country": "Canada"},
        {"city": "Mumbai", "country": "India"},
        {"city": "Singapore", "country": "Singapore"},
        {"city": "Dubai", "country": "UAE"},
        {"city": "São Paulo", "country": "Brazil"},
    ]

    # Event Types
    EVENT_TYPES: list = [
        "product_view",
        "add_to_cart",
        "remove_from_cart",
        "purchase",
        "search"
    ]

    # Payment Methods
    PAYMENT_METHODS: list = [
        "credit_card",
        "debit_card",
        "paypal",
        "apple_pay",
        "google_pay"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()


def get_database_url() -> str:
    """
    Get database URL with proper formatting.
    Railway provides DATABASE_URL, but we may need to adjust it.
    """
    db_url = settings.DATABASE_URL

    # Handle Railway's postgres:// vs postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return db_url


def get_kafka_config() -> dict:
    """Get Kafka configuration dictionary"""
    return {
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
        "topic": settings.KAFKA_TOPIC,
        "consumer_group": settings.KAFKA_CONSUMER_GROUP,
        "partitions": settings.KAFKA_PARTITIONS,
        "replication_factor": settings.KAFKA_REPLICATION_FACTOR,
    }


def get_spark_config() -> dict:
    """Get Spark configuration dictionary"""
    return {
        "app_name": settings.SPARK_APP_NAME,
        "master": settings.SPARK_MASTER,
        "checkpoint_dir": settings.SPARK_CHECKPOINT_DIR,
        "kafka_bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "kafka_topic": settings.KAFKA_TOPIC,
    }


if __name__ == "__main__":
    # Test configuration
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"👨‍💻 Built by {settings.DEVELOPER}")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    print(f"📊 Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    print(f"🗄️  Database: {get_database_url()}")
    print(f"⚡ Spark Master: {settings.SPARK_MASTER}")
    print(f"✅ Configuration loaded successfully!")
