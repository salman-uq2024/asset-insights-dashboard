-- Join the relational CSV tables into an analyst-ready asset base table.

WITH latest_condition AS (
    SELECT
        c.asset_id,
        c.inspection_date,
        c.condition_score,
        c.condition_state,
        c.defect_count,
        c.risk_rating
    FROM condition c
    JOIN (
        SELECT asset_id, MAX(inspection_date) AS max_inspection_date
        FROM condition
        GROUP BY asset_id
    ) latest
        ON c.asset_id = latest.asset_id
       AND c.inspection_date = latest.max_inspection_date
),
cost_rollup AS (
    SELECT
        asset_id,
        SUM(amount_aud) AS total_cost_aud,
        SUM(CASE WHEN linked_work_order_id IS NOT NULL AND linked_work_order_id <> '' THEN amount_aud ELSE 0 END) AS maintenance_spend_aud,
        SUM(CASE WHEN cost_type = 'Operational' THEN amount_aud ELSE 0 END) AS operational_cost_aud,
        SUM(CASE WHEN cost_type IN ('Capital', 'Capital Planned') THEN amount_aud ELSE 0 END) AS capital_cost_aud
    FROM cost
    GROUP BY asset_id
),
maintenance_rollup AS (
    SELECT
        m.asset_id,
        COUNT(*) AS work_order_count,
        SUM(CASE WHEN planned_unplanned = 'Unplanned' THEN 1 ELSE 0 END) AS reactive_work_order_count,
        MAX(work_date) AS last_work_date
    FROM maintenance m
    GROUP BY m.asset_id
)
SELECT
    a.asset_id,
    a.asset_name,
    a.asset_type,
    a.install_date,
    a.expected_life_years,
    ROUND((julianday('2026-03-24') - julianday(a.install_date)) / 365.25, 1) AS age_years,
    ROUND(((julianday('2026-03-24') - julianday(a.install_date)) / 365.25) / a.expected_life_years * 100, 1) AS life_consumed_pct,
    a.replacement_value_aud,
    a.criticality,
    l.suburb,
    l.ward,
    l.precinct,
    l.flood_risk_zone,
    lc.inspection_date AS latest_inspection_date,
    lc.condition_score,
    lc.condition_state,
    lc.defect_count,
    lc.risk_rating,
    COALESCE(mr.work_order_count, 0) AS work_order_count,
    COALESCE(mr.reactive_work_order_count, 0) AS reactive_work_order_count,
    mr.last_work_date,
    ROUND(COALESCE(cr.total_cost_aud, 0), 2) AS total_cost_aud,
    ROUND(COALESCE(cr.maintenance_spend_aud, 0), 2) AS maintenance_spend_aud,
    ROUND(COALESCE(cr.operational_cost_aud, 0), 2) AS operational_cost_aud,
    ROUND(COALESCE(cr.capital_cost_aud, 0), 2) AS capital_cost_aud
FROM assets a
LEFT JOIN locations l
    ON a.asset_id = l.asset_id
LEFT JOIN latest_condition lc
    ON a.asset_id = lc.asset_id
LEFT JOIN maintenance_rollup mr
    ON a.asset_id = mr.asset_id
LEFT JOIN cost_rollup cr
    ON a.asset_id = cr.asset_id
ORDER BY lc.condition_score ASC, capital_cost_aud DESC;
