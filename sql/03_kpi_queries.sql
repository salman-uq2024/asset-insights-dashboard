-- Core KPI queries for an asset planning dashboard.

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
asset_base AS (
    SELECT
        a.asset_id,
        a.asset_type,
        a.replacement_value_aud,
        a.expected_life_years,
        ROUND(((julianday('2026-03-24') - julianday(a.install_date)) / 365.25) / a.expected_life_years * 100, 1) AS life_consumed_pct,
        l.suburb,
        l.flood_risk_zone,
        lc.condition_score,
        lc.condition_state,
        lc.risk_rating
    FROM assets a
    LEFT JOIN locations l
        ON a.asset_id = l.asset_id
    LEFT JOIN latest_condition lc
        ON a.asset_id = lc.asset_id
),
spend_base AS (
    SELECT
        c.asset_id,
        SUM(c.amount_aud) AS total_spend_aud,
        SUM(CASE WHEN c.linked_work_order_id IS NOT NULL AND c.linked_work_order_id <> '' THEN c.amount_aud ELSE 0 END) AS maintenance_spend_aud,
        SUM(CASE WHEN m.planned_unplanned = 'Unplanned' THEN c.amount_aud ELSE 0 END) AS reactive_spend_aud,
        SUM(CASE WHEN c.cost_type = 'Capital Planned' THEN c.amount_aud ELSE 0 END) AS capital_pipeline_aud
    FROM cost c
    LEFT JOIN maintenance m
        ON c.linked_work_order_id = m.work_order_id
    GROUP BY c.asset_id
)
SELECT
    COUNT(*) AS total_assets,
    ROUND(SUM(replacement_value_aud), 2) AS total_replacement_value_aud,
    ROUND(AVG(condition_score), 2) AS average_condition_score,
    SUM(CASE WHEN condition_score < 2.5 THEN 1 ELSE 0 END) AS poor_critical_assets,
    ROUND(100.0 * SUM(CASE WHEN condition_score < 2.5 THEN 1 ELSE 0 END) / COUNT(*), 2) AS poor_critical_share_pct,
    SUM(CASE WHEN life_consumed_pct >= 80 THEN 1 ELSE 0 END) AS assets_past_80pct_life,
    ROUND(SUM(COALESCE(sb.maintenance_spend_aud, 0)), 2) AS total_maintenance_spend_aud,
    ROUND(100.0 * SUM(COALESCE(sb.reactive_spend_aud, 0)) / NULLIF(SUM(COALESCE(sb.maintenance_spend_aud, 0)), 0), 2) AS reactive_maintenance_share_pct,
    ROUND(SUM(COALESCE(sb.capital_pipeline_aud, 0)), 2) AS planned_capital_pipeline_aud
FROM asset_base ab
LEFT JOIN spend_base sb
    ON ab.asset_id = sb.asset_id;

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
spend_base AS (
    SELECT
        c.asset_id,
        SUM(c.amount_aud) AS total_spend_aud,
        SUM(CASE WHEN c.linked_work_order_id IS NOT NULL AND c.linked_work_order_id <> '' THEN c.amount_aud ELSE 0 END) AS maintenance_spend_aud,
        SUM(CASE WHEN m.planned_unplanned = 'Unplanned' THEN c.amount_aud ELSE 0 END) AS reactive_spend_aud,
        SUM(CASE WHEN c.cost_type = 'Capital Planned' THEN c.amount_aud ELSE 0 END) AS capital_pipeline_aud
    FROM cost c
    LEFT JOIN maintenance m
        ON c.linked_work_order_id = m.work_order_id
    GROUP BY c.asset_id
)
SELECT
    a.asset_type,
    COUNT(*) AS asset_count,
    ROUND(AVG(lc.condition_score), 2) AS avg_condition_score,
    SUM(CASE WHEN lc.condition_score < 2.5 THEN 1 ELSE 0 END) AS poor_critical_assets,
    ROUND(SUM(COALESCE(sb.maintenance_spend_aud, 0)), 2) AS maintenance_spend_aud,
    ROUND(SUM(COALESCE(sb.reactive_spend_aud, 0)), 2) AS reactive_spend_aud,
    ROUND(SUM(COALESCE(sb.capital_pipeline_aud, 0)), 2) AS capital_pipeline_aud
FROM assets a
LEFT JOIN latest_condition lc
    ON a.asset_id = lc.asset_id
LEFT JOIN spend_base sb
    ON a.asset_id = sb.asset_id
GROUP BY a.asset_type
ORDER BY capital_pipeline_aud DESC, reactive_spend_aud DESC;
