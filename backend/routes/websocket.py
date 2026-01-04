"""
ShopStream WebSocket Handler

Real-time WebSocket endpoint for pushing live metrics to dashboard.
Updates clients every second with latest analytics data.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set
import asyncio
import json
import logging
from datetime import datetime
from models import get_session
from utils.timescale import TimescaleDBHelper

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts updates.
    Maintains a list of active connections and handles disconnections.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


async def fetch_metrics_data():
    """
    Fetch all metrics data for dashboard update.
    Called every second to get latest data.
    """
    session = get_session()
    try:
        helper = TimescaleDBHelper(session)

        # Fetch all required metrics
        live_metrics = helper.get_live_metrics(minutes=5)
        trending_products = helper.get_trending_products(limit=10, minutes=5)
        funnel = helper.get_conversion_funnel(hours=1)
        alerts = helper.get_active_alerts(limit=10)
        comparison = helper.get_hourly_comparison()
        revenue_trend = helper.get_revenue_trend(hours=1)
        geo_distribution = helper.get_geographic_distribution(limit=10, hours=1)

        return {
            "type": "metrics_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "live": live_metrics,
                "trending_products": trending_products,
                "funnel": funnel,
                "alerts": alerts,
                "comparison": comparison,
                "revenue_trend": revenue_trend,
                "geographic": geo_distribution,
            }
        }

    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": str(e)
        }
    finally:
        session.close()


async def metrics_broadcaster():
    """
    Background task that broadcasts metrics every second.
    Runs continuously while there are active connections.
    """
    logger.info("🚀 Starting metrics broadcaster...")

    while True:
        if len(manager.active_connections) > 0:
            # Fetch latest metrics
            metrics = await fetch_metrics_data()

            # Broadcast to all clients
            await manager.broadcast(metrics)

            logger.debug(f"📊 Broadcast metrics to {len(manager.active_connections)} clients")

        # Wait 1 second before next update
        await asyncio.sleep(1)


# Global broadcaster task
broadcaster_task = None


async def start_broadcaster():
    """Start the metrics broadcaster if not already running"""
    global broadcaster_task

    if broadcaster_task is None or broadcaster_task.done():
        broadcaster_task = asyncio.create_task(metrics_broadcaster())
        logger.info("✅ Metrics broadcaster started")


@router.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metrics updates.

    Connection flow:
    1. Client connects
    2. Server accepts connection
    3. Server sends initial metrics
    4. Server broadcasts updates every 1 second
    5. Client can send heartbeat pings
    6. Connection remains open until client disconnects

    Message format (server → client):
    {
        "type": "metrics_update",
        "timestamp": "2025-01-03T10:30:00.123Z",
        "data": {
            "live": { ... },
            "trending_products": [ ... ],
            "funnel": { ... },
            "alerts": [ ... ],
            ...
        }
    }

    Message format (client → server):
    {
        "type": "ping"
    }
    """
    await manager.connect(websocket)

    # Start broadcaster if not running
    await start_broadcaster()

    try:
        # Send initial metrics immediately
        initial_metrics = await fetch_metrics_data()
        await manager.send_personal_message(initial_metrics, websocket)

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (heartbeat pings)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )

                # Parse message
                try:
                    message = json.loads(data)

                    if message.get("type") == "ping":
                        # Respond to heartbeat
                        await manager.send_personal_message(
                            {
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat()
                            },
                            websocket
                        )
                    elif message.get("type") == "request_update":
                        # Client requests immediate update
                        metrics = await fetch_metrics_data()
                        await manager.send_personal_message(metrics, websocket)

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {data}")

            except asyncio.TimeoutError:
                # No message received in 30 seconds, send heartbeat check
                try:
                    await manager.send_personal_message(
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        websocket
                    )
                except:
                    # Connection is dead
                    break

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
