-- Orders Report: Paid and/or Shipped Orders
-- This report provides comprehensive information about orders that have been paid or shipped,
-- including user details, products, payments, and shipments.

-- Main Orders Report
SELECT
    -- Order Information
    o.id AS order_id,
    o.status AS order_status,
    o.total AS order_total,
    o.created_at AS order_created_at,
    o.updated_at AS order_updated_at,

    -- User Information
    u.id AS user_id,
    u.email AS user_email,
    u.first_name AS user_first_name,
    u.last_name AS user_last_name,

    -- Order Items (aggregated)
    (
        SELECT COUNT(*)
        FROM orders_orderitem oi
        WHERE oi.order_id = o.id
    ) AS total_items,

    (
        SELECT GROUP_CONCAT(
            p.name || ' (x' || oi.quantity || ' @ $' || oi.unit_price || ')',
            ', '
        )
        FROM orders_orderitem oi
        JOIN products_product p ON oi.product_id = p.id
        WHERE oi.order_id = o.id
    ) AS products_summary,

    -- Payment Information (aggregated)
    (
        SELECT COALESCE(SUM(op.amount_applied), 0)
        FROM payments_orderpayment op
        JOIN payments_payment pay ON op.payment_id = pay.id
        WHERE op.order_id = o.id AND pay.status = 'completed'
    ) AS total_paid,

    (
        SELECT GROUP_CONCAT(
            'Payment #' || pay.id || ': $' || op.amount_applied || ' (' || pay.method || ', ' || pay.status || ')',
            '; '
        )
        FROM payments_orderpayment op
        JOIN payments_payment pay ON op.payment_id = pay.id
        WHERE op.order_id = o.id
    ) AS payments_summary,

    -- Shipment Information
    (
        SELECT COUNT(*)
        FROM shipments_shipment s
        WHERE s.order_id = o.id
    ) AS total_shipments,

    (
        SELECT s.status
        FROM shipments_shipment s
        WHERE s.order_id = o.id
        ORDER BY s.created_at DESC
        LIMIT 1
    ) AS latest_shipment_status,

    (
        SELECT s.tracking_number
        FROM shipments_shipment s
        WHERE s.order_id = o.id
        ORDER BY s.created_at DESC
        LIMIT 1
    ) AS tracking_number,

    (
        SELECT s.shipped_at
        FROM shipments_shipment s
        WHERE s.order_id = o.id AND s.shipped_at IS NOT NULL
        ORDER BY s.shipped_at DESC
        LIMIT 1
    ) AS shipped_at,

    (
        SELECT s.delivered_at
        FROM shipments_shipment s
        WHERE s.order_id = o.id AND s.delivered_at IS NOT NULL
        ORDER BY s.delivered_at DESC
        LIMIT 1
    ) AS delivered_at

FROM orders_order o
JOIN users_user u ON o.user_id = u.id

WHERE o.status IN ('paid', 'shipped', 'delivered')

ORDER BY o.created_at DESC;


-- Summary Statistics
SELECT
    'Total Orders' AS metric,
    COUNT(*) AS value
FROM orders_order
WHERE status IN ('paid', 'shipped', 'delivered')

UNION ALL

SELECT
    'Total Revenue' AS metric,
    COALESCE(SUM(total), 0) AS value
FROM orders_order
WHERE status IN ('paid', 'shipped', 'delivered')

UNION ALL

SELECT
    'Orders Pending Shipment' AS metric,
    COUNT(*) AS value
FROM orders_order
WHERE status = 'paid'

UNION ALL

SELECT
    'Orders In Transit' AS metric,
    COUNT(*) AS value
FROM orders_order
WHERE status = 'shipped'

UNION ALL

SELECT
    'Orders Delivered' AS metric,
    COUNT(*) AS value
FROM orders_order
WHERE status = 'delivered';


-- Orders by Status Breakdown
SELECT
    status,
    COUNT(*) AS order_count,
    SUM(total) AS total_revenue
FROM orders_order
WHERE status IN ('paid', 'shipped', 'delivered')
GROUP BY status
ORDER BY
    CASE status
        WHEN 'paid' THEN 1
        WHEN 'shipped' THEN 2
        WHEN 'delivered' THEN 3
    END;


-- Top Products in Paid/Shipped Orders
SELECT
    p.id AS product_id,
    p.name AS product_name,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM orders_orderitem oi
JOIN orders_order o ON oi.order_id = o.id
JOIN products_product p ON oi.product_id = p.id
WHERE o.status IN ('paid', 'shipped', 'delivered')
GROUP BY p.id, p.name
ORDER BY total_quantity_sold DESC
LIMIT 10;


-- Average Order Value by Payment Method
SELECT
    pay.method AS payment_method,
    COUNT(DISTINCT o.id) AS order_count,
    AVG(o.total) AS average_order_value,
    SUM(op.amount_applied) AS total_collected
FROM orders_order o
JOIN payments_orderpayment op ON o.id = op.order_id
JOIN payments_payment pay ON op.payment_id = pay.id
WHERE o.status IN ('paid', 'shipped', 'delivered')
  AND pay.status = 'completed'
GROUP BY pay.method
ORDER BY total_collected DESC;
