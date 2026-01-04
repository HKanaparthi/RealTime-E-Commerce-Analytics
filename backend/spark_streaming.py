"""
ShopStream Spark Streaming Processor

Real-time stream processing with Apache Spark Structured Streaming.
Reads events from Kafka, performs windowed aggregations, detects anomalies,
and writes results to TimescaleDB.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, count, sum as spark_sum, avg, countDistinct,
    current_timestamp, lit, when, expr, unix_timestamp, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType, IntegerType, TimestampType
)
import logging
from config import get_spark_config, get_database_url, settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define event schema (matches Kafka event structure)
EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("product", StructType([
        StructField("id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("category", StringType(), False),
        StructField("price", FloatType(), False),
    ])),
    StructField("quantity", IntegerType()),
    StructField("total_amount", FloatType()),
    StructField("payment_method", StringType()),
    StructField("search_query", StringType()),
    StructField("location", StructType([
        StructField("city", StringType()),
        StructField("country", StringType()),
        StructField("ip", StringType()),
    ])),
])


class ShopStreamProcessor:
    """
    Spark Structured Streaming processor for ShopStream analytics.
    Handles real-time aggregations, trending products, and anomaly detection.
    """

    def __init__(self):
        self.spark = None
        self.config = get_spark_config()
        self.db_url = get_database_url()
        self.init_spark()

    def init_spark(self):
        """Initialize Spark session with Kafka and JDBC support"""
        logger.info("🚀 Initializing Spark session...")
        logger.info(f"👨‍💻 Built by Harsha Kanaparthi\n")

        # Download required JARs if not present
        packages = [
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
            "org.postgresql:postgresql:42.7.1"
        ]

        self.spark = (
            SparkSession.builder
            .appName(self.config["app_name"])
            .master(self.config["master"])
            .config("spark.jars.packages", ",".join(packages))
            .config("spark.sql.streaming.checkpointLocation", self.config["checkpoint_dir"])
            .config("spark.sql.shuffle.partitions", "3")
            .config("spark.streaming.kafka.consumer.cache.enabled", "false")
            .getOrCreate()
        )

        self.spark.sparkContext.setLogLevel("WARN")
        logger.info(f"✅ Spark session initialized: {self.config['app_name']}")

    def read_kafka_stream(self):
        """Read streaming data from Kafka"""
        logger.info(f"📥 Reading from Kafka topic: {self.config['kafka_topic']}")

        kafka_stream = (
            self.spark
            .readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.config["kafka_bootstrap_servers"])
            .option("subscribe", self.config["kafka_topic"])
            .option("startingOffsets", "latest")
            .option("failOnDataLoss", "false")
            .load()
        )

        # Parse JSON events
        events = (
            kafka_stream
            .selectExpr("CAST(value AS STRING) as json")
            .select(from_json(col("json"), EVENT_SCHEMA).alias("data"))
            .select("data.*")
            .withColumn("timestamp", to_timestamp(col("timestamp")))
        )

        return events

    def write_to_timescaledb(self, df, table_name: str, mode: str = "append"):
        """Write DataFrame to TimescaleDB via JDBC"""
        (
            df.write
            .format("jdbc")
            .option("url", self.db_url)
            .option("dbtable", table_name)
            .option("user", self.db_url.split("://")[1].split(":")[0])
            .option("password", self.db_url.split(":")[2].split("@")[0])
            .option("driver", "org.postgresql.Driver")
            .mode(mode)
            .save()
        )

    def process_raw_events(self, events):
        """
        Write raw events to TimescaleDB for storage.
        Flattens nested structures for querying.
        """
        logger.info("💾 Processing raw events...")

        raw_events = events.select(
            col("event_id"),
            col("event_type"),
            col("timestamp"),
            col("user_id"),
            col("session_id"),
            col("product.id").alias("product_id"),
            col("product.name").alias("product_name"),
            col("product.category").alias("product_category"),
            col("product.price").alias("product_price"),
            col("quantity"),
            col("total_amount"),
            col("payment_method"),
            col("location.city").alias("city"),
            col("location.country").alias("country"),
            col("location.ip").alias("ip_address"),
            expr("to_json(struct(*))").alias("raw_data")
        )

        # Write to TimescaleDB (batch mode for now - can be streaming)
        query = (
            raw_events
            .writeStream
            .foreachBatch(lambda batch_df, batch_id:
                batch_df.write
                .format("jdbc")
                .option("url", self.db_url)
                .option("dbtable", "events_raw")
                .option("driver", "org.postgresql.Driver")
                .mode("append")
                .save()
            )
            .outputMode("append")
            .start()
        )

        return query

    def process_1min_metrics(self, events):
        """
        Compute 1-minute windowed metrics.
        Includes sales, traffic, funnel metrics.
        """
        logger.info("📊 Processing 1-minute metrics...")

        metrics_1min = (
            events
            .withWatermark("timestamp", "2 minutes")
            .groupBy(window(col("timestamp"), "1 minute").alias("time_window"))
            .agg(
                # Sales metrics
                spark_sum(when(col("event_type") == "purchase", col("total_amount")).otherwise(0)).alias("total_revenue"),
                count(when(col("event_type") == "purchase", 1)).alias("total_orders"),
                avg(when(col("event_type") == "purchase", col("total_amount")).otherwise(None)).alias("average_order_value"),

                # Traffic metrics
                count(when(col("event_type") == "product_view", 1)).alias("total_views"),
                countDistinct(when(col("event_type") == "product_view", col("user_id"))).alias("unique_users"),
                countDistinct(col("session_id")).alias("unique_sessions"),

                # Funnel metrics
                count(when(col("event_type") == "add_to_cart", 1)).alias("add_to_cart_count"),
                count(when(col("event_type") == "remove_from_cart", 1)).alias("remove_from_cart_count"),
                count(when(col("event_type") == "purchase", 1)).alias("purchase_count"),
                count(when(col("event_type") == "search", 1)).alias("search_count"),
            )
            .select(
                col("time_window.start").alias("time_bucket"),
                col("total_revenue"),
                col("total_orders"),
                col("average_order_value"),
                col("total_views"),
                col("unique_users"),
                col("unique_sessions"),
                col("add_to_cart_count"),
                col("remove_from_cart_count"),
                col("purchase_count"),
                col("search_count"),
                # Calculate conversion rates
                (col("purchase_count") / col("total_views") * 100).alias("conversion_rate"),
                when(col("add_to_cart_count") > 0,
                     (1 - col("purchase_count") / col("add_to_cart_count")) * 100
                ).otherwise(0).alias("cart_abandonment_rate"),
                current_timestamp().alias("created_at")
            )
        )

        # Write to TimescaleDB
        query = (
            metrics_1min
            .writeStream
            .foreachBatch(lambda batch_df, batch_id:
                batch_df.write
                .format("jdbc")
                .option("url", self.db_url)
                .option("dbtable", "metrics_1min")
                .option("driver", "org.postgresql.Driver")
                .mode("append")
                .save()
            )
            .outputMode("append")
            .start()
        )

        return query

    def process_trending_products(self, events):
        """
        Identify trending products based on view velocity.
        Updates every minute with top 20 products.
        """
        logger.info("🔥 Processing trending products...")

        product_views = (
            events
            .filter(col("event_type").isin(["product_view", "purchase"]))
            .withWatermark("timestamp", "2 minutes")
            .groupBy(
                window(col("timestamp"), "1 minute").alias("time_window"),
                col("product.id").alias("product_id"),
                col("product.name").alias("product_name"),
                col("product.category").alias("product_category"),
                col("product.price").alias("product_price")
            )
            .agg(
                count(when(col("event_type") == "product_view", 1)).alias("view_count"),
                count(when(col("event_type") == "purchase", 1)).alias("purchase_count"),
                spark_sum(when(col("event_type") == "purchase", col("total_amount")).otherwise(0)).alias("revenue"),
            )
            .select(
                col("time_window.start").alias("time_bucket"),
                col("product_id"),
                col("product_name"),
                col("product_category"),
                col("product_price"),
                col("view_count"),
                col("purchase_count"),
                col("revenue"),
                col("view_count").alias("views_per_minute"),  # Already 1-min window
                (col("view_count") * 10 + col("purchase_count") * 50).alias("trending_score"),  # Weighted score
                current_timestamp().alias("updated_at")
            )
        )

        # Write to TimescaleDB
        query = (
            product_views
            .writeStream
            .foreachBatch(lambda batch_df, batch_id:
                batch_df.write
                .format("jdbc")
                .option("url", self.db_url)
                .option("dbtable", "trending_products")
                .option("driver", "org.postgresql.Driver")
                .mode("append")
                .save()
            )
            .outputMode("append")
            .start()
        )

        return query

    def process_geographic_metrics(self, events):
        """
        Aggregate metrics by geographic location (country, city).
        """
        logger.info("🌍 Processing geographic metrics...")

        geo_metrics = (
            events
            .filter(col("location").isNotNull())
            .withWatermark("timestamp", "2 minutes")
            .groupBy(
                window(col("timestamp"), "1 minute").alias("time_window"),
                col("location.country").alias("country"),
                col("location.city").alias("city")
            )
            .agg(
                count(when(col("event_type") == "product_view", 1)).alias("total_views"),
                count(when(col("event_type") == "purchase", 1)).alias("total_orders"),
                spark_sum(when(col("event_type") == "purchase", col("total_amount")).otherwise(0)).alias("total_revenue"),
                countDistinct(col("user_id")).alias("unique_users"),
            )
            .select(
                col("time_window.start").alias("time_bucket"),
                col("country"),
                col("city"),
                col("total_views"),
                col("total_orders"),
                col("total_revenue"),
                col("unique_users"),
                current_timestamp().alias("updated_at")
            )
        )

        # Write to TimescaleDB
        query = (
            geo_metrics
            .writeStream
            .foreachBatch(lambda batch_df, batch_id:
                batch_df.write
                .format("jdbc")
                .option("url", self.db_url)
                .option("dbtable", "geographic_metrics")
                .option("driver", "org.postgresql.Driver")
                .mode("append")
                .save()
            )
            .outputMode("append")
            .start()
        )

        return query

    def start(self):
        """
        Start all streaming queries.
        Runs indefinitely until stopped.
        """
        logger.info("⚡ Starting ShopStream processor...")

        # Read events from Kafka
        events = self.read_kafka_stream()

        # Start all processing queries
        queries = []

        # 1. Raw events storage
        queries.append(self.process_raw_events(events))

        # 2. 1-minute metrics
        queries.append(self.process_1min_metrics(events))

        # 3. Trending products
        queries.append(self.process_trending_products(events))

        # 4. Geographic metrics
        queries.append(self.process_geographic_metrics(events))

        logger.info(f"✅ All {len(queries)} streaming queries started!")
        logger.info("📊 Processing events in real-time...")
        logger.info("⏹️  Press Ctrl+C to stop\n")

        # Wait for termination
        try:
            for query in queries:
                query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping Spark streaming (Ctrl+C)")
            for query in queries:
                query.stop()
            self.spark.stop()
            logger.info("✅ Spark session closed")


def main():
    """Main entry point for Spark streaming processor"""
    try:
        processor = ShopStreamProcessor()
        processor.start()
    except Exception as e:
        logger.error(f"❌ Error in Spark streaming: {e}")
        raise


if __name__ == "__main__":
    main()
