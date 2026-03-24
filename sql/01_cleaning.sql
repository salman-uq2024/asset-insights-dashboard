-- SQLite-friendly cleaning layer for imported CSV tables:
-- assets, locations, condition, maintenance, cost

WITH assets_clean AS (
    SELECT
        TRIM(asset_id) AS asset_id,
        TRIM(asset_name) AS asset_name,
        TRIM(asset_type) AS asset_type,
        date(install_date) AS install_date,
        CAST(expected_life_years AS INTEGER) AS expected_life_years,
        ROUND(CAST(replacement_value_aud AS REAL), 2) AS replacement_value_aud,
        TRIM(criticality) AS criticality,
        TRIM(owner_department) AS owner_department,
        TRIM(status) AS status
    FROM assets
    WHERE TRIM(asset_id) <> ''
),
locations_clean AS (
    SELECT
        TRIM(location_id) AS location_id,
        TRIM(asset_id) AS asset_id,
        TRIM(suburb) AS suburb,
        TRIM(ward) AS ward,
        TRIM(precinct) AS precinct,
        ROUND(CAST(latitude AS REAL), 6) AS latitude,
        ROUND(CAST(longitude AS REAL), 6) AS longitude,
        CASE
            WHEN LOWER(TRIM(flood_risk_zone)) IN ('high', 'moderate', 'low') THEN
                UPPER(SUBSTR(TRIM(flood_risk_zone), 1, 1)) || LOWER(SUBSTR(TRIM(flood_risk_zone), 2))
            ELSE 'Low'
        END AS flood_risk_zone
    FROM locations
),
condition_clean AS (
    SELECT
        TRIM(inspection_id) AS inspection_id,
        TRIM(asset_id) AS asset_id,
        date(inspection_date) AS inspection_date,
        ROUND(CAST(condition_score AS REAL), 1) AS condition_score,
        TRIM(condition_state) AS condition_state,
        CAST(defect_count AS INTEGER) AS defect_count,
        TRIM(risk_rating) AS risk_rating,
        TRIM(inspector) AS inspector
    FROM condition
),
maintenance_clean AS (
    SELECT
        TRIM(work_order_id) AS work_order_id,
        TRIM(asset_id) AS asset_id,
        date(work_date) AS work_date,
        TRIM(maintenance_type) AS maintenance_type,
        TRIM(priority) AS priority,
        CASE
            WHEN LOWER(TRIM(planned_unplanned)) = 'unplanned' THEN 'Unplanned'
            ELSE 'Planned'
        END AS planned_unplanned,
        TRIM(status) AS status,
        ROUND(CAST(labor_hours AS REAL), 1) AS labor_hours,
        CASE
            WHEN LOWER(TRIM(contractor_used)) = 'yes' THEN 'Yes'
            ELSE 'No'
        END AS contractor_used,
        TRIM(defect_category) AS defect_category
    FROM maintenance
),
cost_clean AS (
    SELECT
        TRIM(cost_id) AS cost_id,
        TRIM(asset_id) AS asset_id,
        date(cost_date) AS cost_date,
        TRIM(cost_type) AS cost_type,
        ROUND(CAST(amount_aud AS REAL), 2) AS amount_aud,
        TRIM(funding_source) AS funding_source,
        NULLIF(TRIM(linked_work_order_id), '') AS linked_work_order_id,
        TRIM(fiscal_year) AS fiscal_year
    FROM cost
)
SELECT 'assets_clean' AS cleaned_table, COUNT(*) AS row_count FROM assets_clean
UNION ALL
SELECT 'locations_clean', COUNT(*) FROM locations_clean
UNION ALL
SELECT 'condition_clean', COUNT(*) FROM condition_clean
UNION ALL
SELECT 'maintenance_clean', COUNT(*) FROM maintenance_clean
UNION ALL
SELECT 'cost_clean', COUNT(*) FROM cost_clean;
