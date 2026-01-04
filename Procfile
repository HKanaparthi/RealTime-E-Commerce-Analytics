# ShopStream Procfile for Railway

# Main API server
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT

# Event generator (optional - can be run separately)
# worker: cd backend && python kafka_producer.py --rate 100

# Spark streaming (optional - can be run separately)
# spark: cd backend && python spark_streaming.py
