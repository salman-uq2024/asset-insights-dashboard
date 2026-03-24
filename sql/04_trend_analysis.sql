-- Trend analysis for deterioration, maintenance workload, and place-based risk.

SELECT
    substr(c.inspection_date, 1, 4) AS inspection_year,
    a.asset_type,
    ROUND(AVG(c.condition_score), 2) AS avg_condition_score,
    SUM(CASE WHEN c.condition_score < 2.5 THEN 1 ELSE 0 END) AS poor_critical_assets
FROM condition c
JOIN assets a
    ON c.asset_id = a.asset_id
GROUP BY substr(c.inspection_date, 1, 4), a.asset_type
ORDER BY inspection_year, a.asset_type;

SELECT
    substr(m.work_date, 1, 7) AS work_month,
    COUNT(*) AS work_orders,
    ROUND(SUM(COALESCE(c.amount_aud, 0)), 2) AS total_spend_aud,
    ROUND(SUM(CASE WHEN m.planned_unplanned = 'Unplanned' THEN COALESCE(c.amount_aud, 0) ELSE 0 END), 2) AS reactive_spend_aud,
    ROUND(100.0 * SUM(CASE WHEN m.planned_unplanned = 'Unplanned' THEN COALESCE(c.amount_aud, 0) ELSE 0 END) / NULLIF(SUM(COALESCE(c.amount_aud, 0)), 0), 2) AS reactive_share_pct
FROM maintenance m
LEFT JOIN cost c
    ON m.work_order_id = c.linked_work_order_id
GROUP BY substr(m.work_date, 1, 7)
ORDER BY work_month;

WITH latest_condition AS (
    SELECT c.*
    FROM condition c
    JOIN (
        SELECT asset_id, MAX(inspection_date) AS max_inspection_date
        FROM condition
        GROUP BY asset_id
    ) latest
        ON c.asset_id = latest.asset_id
       AND c.inspection_date = latest.max_inspection_date
),
reactive_spend AS (
    SELECT
        m.asset_id,
        SUM(COALESCE(c.amount_aud, 0)) AS reactive_spend_aud
    FROM maintenance m
    LEFT JOIN cost c
        ON m.work_order_id = c.linked_work_order_id
    WHERE m.planned_unplanned = 'Unplanned'
    GROUP BY m.asset_id
)
SELECT
    l.suburb,
    l.flood_risk_zone,
    COUNT(*) AS asset_count,
    ROUND(AVG(lc.condition_score), 2) AS avg_condition_score,
    SUM(CASE WHEN lc.risk_rating IN ('High', 'Critical') THEN 1 ELSE 0 END) AS high_risk_assets,
    ROUND(SUM(COALESCE(rs.reactive_spend_aud, 0)), 2) AS reactive_spend_aud
FROM assets a
JOIN locations l
    ON a.asset_id = l.asset_id
JOIN latest_condition lc
    ON a.asset_id = lc.asset_id
LEFT JOIN reactive_spend rs
    ON a.asset_id = rs.asset_id
GROUP BY l.suburb, l.flood_risk_zone
ORDER BY high_risk_assets DESC, reactive_spend_aud DESC;
