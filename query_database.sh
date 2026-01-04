#!/bin/bash
# ShopStream Database Query Helper
# Built by Harsha Kanaparthi

echo "🗄️  ShopStream Database Query Tool"
echo "=================================="
echo ""

if [ -z "$1" ]; then
    echo "Usage:"
    echo "  ./query_database.sh shell              # Open interactive SQL shell"
    echo "  ./query_database.sh stats              # Show quick stats"
    echo "  ./query_database.sh tables             # List all tables"
    echo "  ./query_database.sh events             # Show recent events"
    echo "  ./query_database.sh metrics            # Show latest metrics"
    echo "  ./query_database.sh alerts             # Show active alerts"
    echo "  ./query_database.sh purchases          # Show recent purchases"
    echo "  ./query_database.sh \"CUSTOM SQL\"       # Run custom SQL query"
    echo ""
    exit 1
fi

CONTAINER="shopstream-timescaledb"
DB_USER="postgres"
DB_NAME="shopstream"

case "$1" in
    shell)
        echo "Opening interactive SQL shell..."
        echo "Commands: \\dt (list tables), \\q (quit)"
        docker exec -it $CONTAINER psql -U $DB_USER -d $DB_NAME
        ;;

    stats)
        echo "📊 Database Statistics:"
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "
            SELECT
                'Total Events' as metric,
                COUNT(*)::text as value
            FROM events_raw
            UNION ALL
            SELECT
                'Total Revenue',
                '$' || ROUND(SUM(total_amount))::text
            FROM events_raw
            WHERE event_type = 'purchase'
            UNION ALL
            SELECT
                'Total Purchases',
                COUNT(*)::text
            FROM events_raw
            WHERE event_type = 'purchase'
            UNION ALL
            SELECT
                'Unique Users',
                COUNT(DISTINCT user_id)::text
            FROM events_raw
            UNION ALL
            SELECT
                'Active Alerts',
                COUNT(*)::text
            FROM alerts
            WHERE is_active = true;
        "
        ;;

    tables)
        echo "📋 Database Tables:"
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "\dt"
        ;;

    events)
        echo "📝 Recent Events (Last 10):"
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "
            SELECT
                event_type,
                timestamp,
                user_id,
                product_name,
                total_amount
            FROM events_raw
            ORDER BY timestamp DESC
            LIMIT 10;
        "
        ;;

    metrics)
        echo "📈 Latest Metrics:"
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "
            SELECT
                time_bucket,
                total_revenue,
                total_orders,
                unique_users,
                conversion_rate,
                cart_abandonment_rate
            FROM metrics_1min
            ORDER BY time_bucket DESC
            LIMIT 10;
        "
        ;;

    alerts)
        echo "⚠️  Active Alerts:"
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "
            SELECT
                alert_type,
                severity,
                title,
                detected_at
            FROM alerts
            WHERE is_active = true
            ORDER BY detected_at DESC
            LIMIT 10;
        "
        ;;

    purchases)
        echo "🛒 Recent Purchases:"
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "
            SELECT
                timestamp,
                user_id,
                product_name,
                total_amount
            FROM events_raw
            WHERE event_type = 'purchase'
            ORDER BY timestamp DESC
            LIMIT 10;
        "
        ;;

    *)
        echo "🔍 Running custom query..."
        docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "$1"
        ;;
esac
