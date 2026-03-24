# Data Dictionary

This project uses five raw relational-style tables and six prepared dashboard outputs.

## Raw Tables

### `assets.csv`

| Column | Type | Description |
| --- | --- | --- |
| `asset_id` | Text | Unique asset identifier. |
| `asset_name` | Text | Human-readable asset label. |
| `asset_type` | Text | Asset class such as Road Segment, Bridge, or Community Building. |
| `install_date` | Date | Commissioning or install date. |
| `expected_life_years` | Integer | Nominal useful life used for lifecycle analysis. |
| `replacement_value_aud` | Decimal | Estimated replacement cost in Australian dollars. |
| `criticality` | Text | Service criticality rating: Medium, High, or Critical. |
| `owner_department` | Text | Council business unit responsible for the asset. |
| `status` | Text | Operational status. |

### `locations.csv`

| Column | Type | Description |
| --- | --- | --- |
| `location_id` | Text | Unique location row identifier. |
| `asset_id` | Text | Foreign key to `assets.asset_id`. |
| `suburb` | Text | Suburb or service locality. |
| `ward` | Text | Council ward or reporting district. |
| `precinct` | Text | Simplified planning precinct. |
| `latitude` | Decimal | Approximate latitude for mapping. |
| `longitude` | Decimal | Approximate longitude for mapping. |
| `flood_risk_zone` | Text | Flood exposure grouping: Low, Moderate, or High. |

### `condition.csv`

| Column | Type | Description |
| --- | --- | --- |
| `inspection_id` | Text | Unique inspection identifier. |
| `asset_id` | Text | Foreign key to `assets.asset_id`. |
| `inspection_date` | Date | Inspection or condition assessment date. |
| `condition_score` | Decimal | Asset condition score on a 1 to 5 scale. |
| `condition_state` | Text | Label derived from the score: Excellent to Critical. |
| `defect_count` | Integer | Count of observed defects or issues. |
| `risk_rating` | Text | Combined risk view derived from condition, criticality, and flood exposure. |
| `inspector` | Text | Assessor name. |

### `maintenance.csv`

| Column | Type | Description |
| --- | --- | --- |
| `work_order_id` | Text | Unique maintenance work order identifier. |
| `asset_id` | Text | Foreign key to `assets.asset_id`. |
| `work_date` | Date | Completion date for the work order. |
| `maintenance_type` | Text | Work type such as Preventive Maintenance, Reactive Repair, or Emergency Repair. |
| `priority` | Text | Work priority. |
| `planned_unplanned` | Text | Planned or unplanned classification. |
| `status` | Text | Work order status. |
| `labor_hours` | Decimal | Estimated labour hours used. |
| `contractor_used` | Text | Indicates whether an external contractor was used. |
| `defect_category` | Text | Primary issue or defect category. |

### `cost.csv`

| Column | Type | Description |
| --- | --- | --- |
| `cost_id` | Text | Unique cost transaction identifier. |
| `asset_id` | Text | Foreign key to `assets.asset_id`. |
| `cost_date` | Date | Transaction date. |
| `cost_type` | Text | Operational, Capital, or Capital Planned. |
| `amount_aud` | Decimal | Cost amount in Australian dollars. |
| `funding_source` | Text | Budget source such as Operating Budget or Renewal Program. |
| `linked_work_order_id` | Text | Optional link to `maintenance.work_order_id`. Blank means the cost is not tied to a completed work order. |
| `fiscal_year` | Text | Fiscal year label. |

## Dashboard Outputs

### `kpi_summary.csv`

| Column | Type | Description |
| --- | --- | --- |
| `metric` | Text | KPI name. |
| `value` | Text | KPI result stored as text for easy BI ingestion. |
| `note` | Text | Business explanation of the KPI. |

### `asset_type_summary.csv`

| Column | Type | Description |
| --- | --- | --- |
| `asset_type` | Text | Asset class. |
| `asset_count` | Integer | Number of assets in the class. |
| `avg_condition_score` | Decimal | Latest average condition score. |
| `poor_critical_assets` | Integer | Count of assets with latest condition below 2.5. |
| `maintenance_spend_aud` | Decimal | Completed maintenance spend linked to work orders. |
| `reactive_cost_aud` | Decimal | Unplanned maintenance spend linked to work orders. |
| `capital_pipeline_aud` | Decimal | Planned future capital pipeline estimate. |

### `suburb_risk_summary.csv`

| Column | Type | Description |
| --- | --- | --- |
| `suburb` | Text | Suburb or locality. |
| `asset_count` | Integer | Number of assets in the suburb. |
| `avg_condition_score` | Decimal | Latest average condition score. |
| `poor_critical_assets` | Integer | Count of poor / critical assets. |
| `high_flood_risk_assets` | Integer | Count of assets in high flood-risk zones. |
| `maintenance_spend_aud` | Decimal | Completed maintenance spend linked to work orders. |
| `reactive_cost_aud` | Decimal | Unplanned maintenance spend. |
| `capital_pipeline_aud` | Decimal | Planned future capital pipeline estimate. |

### `monthly_maintenance_trend.csv`

| Column | Type | Description |
| --- | --- | --- |
| `work_month` | Text | Year-month bucket. |
| `total_work_orders` | Integer | Number of work orders completed in the month. |
| `total_cost_aud` | Decimal | Total linked maintenance spend in the month. |
| `reactive_share_pct` | Decimal | Share of monthly spend tied to unplanned work. |

### `annual_condition_trend.csv`

| Column | Type | Description |
| --- | --- | --- |
| `inspection_year` | Text | Calendar year of inspection. |
| `asset_type` | Text | Asset class. |
| `avg_condition_score` | Decimal | Average condition in the year. |
| `poor_critical_assets` | Integer | Count of poor / critical records in the year. |

### `renewal_priority_register.csv`

| Column | Type | Description |
| --- | --- | --- |
| `asset_id` | Text | Unique asset identifier. |
| `asset_name` | Text | Human-readable asset name. |
| `asset_type` | Text | Asset class. |
| `suburb` | Text | Asset suburb. |
| `criticality` | Text | Service criticality rating. |
| `flood_risk_zone` | Text | Flood exposure grouping. |
| `latest_condition_score` | Decimal | Most recent condition score. |
| `latest_condition_state` | Text | Most recent condition label. |
| `latest_risk_rating` | Text | Most recent combined risk rating. |
| `age_years` | Decimal | Asset age in years. |
| `life_consumed_pct` | Decimal | Estimated share of expected life consumed. |
| `reactive_cost_24m_aud` | Decimal | Reactive spend over the recent 24-month window. |
| `capital_pipeline_aud` | Decimal | Planned capital estimate associated with the asset. |
| `priority_score` | Decimal | Composite renewal priority score. |
| `recommendation` | Text | Analyst-facing action suggestion. |
