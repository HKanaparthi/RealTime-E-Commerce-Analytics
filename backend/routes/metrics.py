"""
ShopStream Metrics API Routes

REST API endpoints for querying real-time analytics metrics.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
from models import get_session
from utils.timescale import TimescaleDBHelper
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def get_db():
    """Dependency for database session"""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.get("/live")
async def get_live_metrics(
    minutes: int = Query(5, ge=1, le=60, description="Number of minutes to analyze"),
    session=Depends(get_db)
):
    """
    Get live metrics for the last N minutes.
    Returns real-time KPIs for dashboard display.

    Example response:
    {
        "revenue": 45234.50,
        "orders": 142,
        "active_users": 47,
        "conversion_rate": 7.1,
        "cart_abandonment_rate": 65.3
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        metrics = helper.get_live_metrics(minutes=minutes)
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching live metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue")
async def get_revenue_trend(
    hours: int = Query(1, ge=1, le=24, description="Number of hours to analyze"),
    session=Depends(get_db)
):
    """
    Get revenue trend over time.
    Returns time-series data for charting.

    Example response:
    {
        "success": true,
        "data": [
            {
                "timestamp": "2025-01-03T10:00:00",
                "revenue": 1234.50,
                "orders": 12,
                "average_order_value": 102.88
            },
            ...
        ]
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        trend = helper.get_revenue_trend(hours=hours)
        return {
            "success": True,
            "data": trend,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching revenue trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/trending")
async def get_trending_products(
    limit: int = Query(10, ge=1, le=50, description="Number of products to return"),
    minutes: int = Query(5, ge=1, le=60, description="Time window in minutes"),
    session=Depends(get_db)
):
    """
    Get trending products ranked by views and purchases.

    Example response:
    {
        "success": true,
        "data": [
            {
                "product_id": "prod_001",
                "product_name": "iPhone 15 Pro",
                "category": "Electronics",
                "price": 999.00,
                "views": 45,
                "purchases": 8,
                "revenue": 7992.00,
                "views_per_minute": 9.0,
                "trending_score": 850.0,
                "rank": 1
            },
            ...
        ]
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        products = helper.get_trending_products(limit=limit, minutes=minutes)
        return {
            "success": True,
            "data": products,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching trending products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funnel")
async def get_conversion_funnel(
    hours: int = Query(1, ge=1, le=24, description="Time window in hours"),
    session=Depends(get_db)
):
    """
    Get conversion funnel metrics (views → cart → purchase).

    Example response:
    {
        "success": true,
        "data": {
            "views": 1247,
            "add_to_cart": 312,
            "purchases": 89,
            "cart_rate": 25.0,
            "conversion_rate": 7.1
        }
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        funnel = helper.get_conversion_funnel(hours=hours)
        return {
            "success": True,
            "data": funnel,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching conversion funnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geographic")
async def get_geographic_distribution(
    limit: int = Query(10, ge=1, le=50, description="Number of locations to return"),
    hours: int = Query(1, ge=1, le=24, description="Time window in hours"),
    session=Depends(get_db)
):
    """
    Get geographic sales distribution.

    Example response:
    {
        "success": true,
        "data": [
            {
                "country": "USA",
                "city": "New York",
                "revenue": 15234.50,
                "orders": 78,
                "views": 456,
                "users": 123
            },
            ...
        ]
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        geo_data = helper.get_geographic_distribution(limit=limit, hours=hours)
        return {
            "success": True,
            "data": geo_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching geographic distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(
    limit: int = Query(10, ge=1, le=50, description="Number of alerts to return"),
    session=Depends(get_db)
):
    """
    Get active alerts (not yet resolved).

    Example response:
    {
        "success": true,
        "data": [
            {
                "id": 123,
                "type": "traffic_spike",
                "severity": "warning",
                "title": "Traffic Spike Detected (+150%)",
                "description": "Traffic increased from 100 to 250 views...",
                "metric": "total_views",
                "current_value": 250.0,
                "threshold": 100.0,
                "change_percent": 150.0,
                "product": null,
                "detected_at": "2025-01-03T10:15:00"
            },
            ...
        ]
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        alerts = helper.get_active_alerts(limit=limit)
        return {
            "success": True,
            "data": alerts,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison")
async def get_hourly_comparison(session=Depends(get_db)):
    """
    Compare current hour vs previous hour.
    Returns percentage changes for key metrics.

    Example response:
    {
        "success": true,
        "data": {
            "revenue_change_percent": 23.5,
            "orders_change_percent": 18.2,
            "current_revenue": 5432.10,
            "current_orders": 42
        }
    }
    """
    try:
        helper = TimescaleDBHelper(session)
        comparison = helper.get_hourly_comparison()
        return {
            "success": True,
            "data": comparison,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching hourly comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "success": True,
        "status": "healthy",
        "service": "ShopStream API",
        "developer": "Harsha Kanaparthi",
        "timestamp": datetime.utcnow().isoformat(),
    }
