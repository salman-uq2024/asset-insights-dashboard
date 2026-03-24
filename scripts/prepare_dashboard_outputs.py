#!/usr/bin/env python3
"""Prepare dashboard-ready outputs from the portfolio sample CSVs."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "dashboard"


TABLE_DEFINITIONS: dict[str, tuple[str, list[str]]] = {
    "assets": (
        """
        CREATE TABLE assets (
            asset_id TEXT PRIMARY KEY,
            asset_name TEXT,
            asset_type TEXT,
            install_date TEXT,
            expected_life_years INTEGER,
            replacement_value_aud REAL,
            criticality TEXT,
            owner_department TEXT,
            status TEXT
        )
        """,
        [
            "asset_id",
            "asset_name",
            "asset_type",
            "install_date",
            "expected_life_years",
            "replacement_value_aud",
            "criticality",
            "owner_department",
            "status",
        ],
    ),
    "locations": (
        """
        CREATE TABLE locations (
            location_id TEXT PRIMARY KEY,
            asset_id TEXT,
            suburb TEXT,
            ward TEXT,
            precinct TEXT,
            latitude REAL,
            longitude REAL,
            flood_risk_zone TEXT
        )
        """,
        [
            "location_id",
            "asset_id",
            "suburb",
            "ward",
            "precinct",
            "latitude",
            "longitude",
            "flood_risk_zone",
        ],
    ),
    "condition": (
        """
        CREATE TABLE condition (
            inspection_id TEXT PRIMARY KEY,
            asset_id TEXT,
            inspection_date TEXT,
            condition_score REAL,
            condition_state TEXT,
            defect_count INTEGER,
            risk_rating TEXT,
            inspector TEXT
        )
        """,
        [
            "inspection_id",
            "asset_id",
            "inspection_date",
            "condition_score",
            "condition_state",
            "defect_count",
            "risk_rating",
            "inspector",
        ],
    ),
    "maintenance": (
        """
        CREATE TABLE maintenance (
            work_order_id TEXT PRIMARY KEY,
            asset_id TEXT,
            work_date TEXT,
            maintenance_type TEXT,
            priority TEXT,
            planned_unplanned TEXT,
            status TEXT,
            labor_hours REAL,
            contractor_used TEXT,
            defect_category TEXT
        )
        """,
        [
            "work_order_id",
            "asset_id",
            "work_date",
            "maintenance_type",
            "priority",
            "planned_unplanned",
            "status",
            "labor_hours",
            "contractor_used",
            "defect_category",
        ],
    ),
    "cost": (
        """
        CREATE TABLE cost (
            cost_id TEXT PRIMARY KEY,
            asset_id TEXT,
            cost_date TEXT,
            cost_type TEXT,
            amount_aud REAL,
            funding_source TEXT,
            linked_work_order_id TEXT,
            fiscal_year TEXT
        )
        """,
        [
            "cost_id",
            "asset_id",
            "cost_date",
            "cost_type",
            "amount_aud",
            "funding_source",
            "linked_work_order_id",
            "fiscal_year",
        ],
    ),
}

BASE_CTES = """
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
    ) max_c
        ON c.asset_id = max_c.asset_id
       AND c.inspection_date = max_c.max_inspection_date
),
cost_rollup AS (
    SELECT
        asset_id,
        SUM(amount_aud) AS total_cost_aud,
        SUM(CASE WHEN linked_work_order_id IS NOT NULL AND linked_work_order_id <> '' THEN amount_aud ELSE 0 END) AS maintenance_spend_aud,
        SUM(CASE WHEN cost_type = 'Operational' THEN amount_aud ELSE 0 END) AS operational_cost_aud,
        SUM(CASE WHEN cost_type = 'Capital' THEN amount_aud ELSE 0 END) AS capital_cost_aud,
        SUM(CASE WHEN cost_type = 'Capital Planned' THEN amount_aud ELSE 0 END) AS capital_pipeline_aud
    FROM cost
    GROUP BY asset_id
),
reactive_rollup AS (
    SELECT
        m.asset_id,
        COUNT(*) AS reactive_work_orders,
        SUM(COALESCE(c.amount_aud, 0)) AS reactive_cost_aud
    FROM maintenance m
    LEFT JOIN cost c
        ON m.work_order_id = c.linked_work_order_id
    WHERE m.planned_unplanned = 'Unplanned'
    GROUP BY m.asset_id
),
recent_reactive_rollup AS (
    SELECT
        m.asset_id,
        SUM(COALESCE(c.amount_aud, 0)) AS reactive_cost_24m_aud
    FROM maintenance m
    LEFT JOIN cost c
        ON m.work_order_id = c.linked_work_order_id
    WHERE m.planned_unplanned = 'Unplanned'
      AND date(m.work_date) >= date('2024-01-01')
    GROUP BY m.asset_id
),
asset_base AS (
    SELECT
        a.asset_id,
        a.asset_name,
        a.asset_type,
        a.install_date,
        a.expected_life_years,
        a.replacement_value_aud,
        a.criticality,
        a.owner_department,
        l.suburb,
        l.ward,
        l.precinct,
        l.flood_risk_zone,
        lc.inspection_date AS latest_inspection_date,
        lc.condition_score AS latest_condition_score,
        lc.condition_state AS latest_condition_state,
        lc.defect_count AS latest_defect_count,
        lc.risk_rating AS latest_risk_rating,
        ROUND((julianday('2026-03-24') - julianday(a.install_date)) / 365.25, 1) AS age_years,
        ROUND(((julianday('2026-03-24') - julianday(a.install_date)) / 365.25) / a.expected_life_years * 100, 1) AS life_consumed_pct,
        COALESCE(cr.total_cost_aud, 0) AS total_cost_aud,
        COALESCE(cr.maintenance_spend_aud, 0) AS maintenance_spend_aud,
        COALESCE(cr.operational_cost_aud, 0) AS operational_cost_aud,
        COALESCE(cr.capital_cost_aud, 0) AS capital_cost_aud,
        COALESCE(cr.capital_pipeline_aud, 0) AS capital_pipeline_aud,
        COALESCE(rr.reactive_work_orders, 0) AS reactive_work_orders,
        COALESCE(rr.reactive_cost_aud, 0) AS reactive_cost_aud,
        COALESCE(rr24.reactive_cost_24m_aud, 0) AS reactive_cost_24m_aud
    FROM assets a
    LEFT JOIN locations l
        ON a.asset_id = l.asset_id
    LEFT JOIN latest_condition lc
        ON a.asset_id = lc.asset_id
    LEFT JOIN cost_rollup cr
        ON a.asset_id = cr.asset_id
    LEFT JOIN reactive_rollup rr
        ON a.asset_id = rr.asset_id
    LEFT JOIN recent_reactive_rollup rr24
        ON a.asset_id = rr24.asset_id
)
"""

OUTPUT_QUERIES = {
    "kpi_summary.csv": BASE_CTES
    + """
    SELECT 'Total assets' AS metric, CAST(COUNT(*) AS TEXT) AS value, 'Current active portfolio' AS note
    FROM asset_base
    UNION ALL
    SELECT 'Total replacement value (AUD)', printf('%.2f', SUM(replacement_value_aud)), 'Portfolio replacement value'
    FROM asset_base
    UNION ALL
    SELECT 'Average latest condition score', printf('%.2f', AVG(latest_condition_score)), '5 = excellent, 1 = critical'
    FROM asset_base
    UNION ALL
    SELECT 'Poor or critical assets', CAST(SUM(CASE WHEN latest_condition_score < 2.5 THEN 1 ELSE 0 END) AS TEXT), 'Assets requiring intervention'
    FROM asset_base
    UNION ALL
    SELECT 'Poor or critical share (%)', printf('%.2f', 100.0 * SUM(CASE WHEN latest_condition_score < 2.5 THEN 1 ELSE 0 END) / COUNT(*)), 'Risk exposure in current portfolio'
    FROM asset_base
    UNION ALL
    SELECT 'Total maintenance spend (AUD)', printf('%.2f', SUM(maintenance_spend_aud)), 'Completed work order spend'
    FROM asset_base
    UNION ALL
    SELECT 'Reactive maintenance share (%)', printf('%.2f', 100.0 * SUM(reactive_cost_aud) / NULLIF(SUM(maintenance_spend_aud), 0)), 'Share of maintenance spend that is unplanned'
    FROM asset_base
    UNION ALL
    SELECT 'Assets past 80% of expected life', CAST(SUM(CASE WHEN life_consumed_pct >= 80 THEN 1 ELSE 0 END) AS TEXT), 'Age-based renewal pressure'
    FROM asset_base
    UNION ALL
    SELECT 'Planned capital pipeline (AUD)', printf('%.2f', SUM(capital_pipeline_aud)), 'Forward renewal estimate'
    FROM asset_base
    """,
    "asset_type_summary.csv": BASE_CTES
    + """
    SELECT
        asset_type,
        COUNT(*) AS asset_count,
        ROUND(AVG(latest_condition_score), 2) AS avg_condition_score,
        SUM(CASE WHEN latest_condition_score < 2.5 THEN 1 ELSE 0 END) AS poor_critical_assets,
        ROUND(SUM(maintenance_spend_aud), 2) AS maintenance_spend_aud,
        ROUND(SUM(reactive_cost_aud), 2) AS reactive_cost_aud,
        ROUND(SUM(capital_pipeline_aud), 2) AS capital_pipeline_aud
    FROM asset_base
    GROUP BY asset_type
    ORDER BY capital_pipeline_aud DESC, reactive_cost_aud DESC
    """,
    "suburb_risk_summary.csv": BASE_CTES
    + """
    SELECT
        suburb,
        COUNT(*) AS asset_count,
        ROUND(AVG(latest_condition_score), 2) AS avg_condition_score,
        SUM(CASE WHEN latest_condition_score < 2.5 THEN 1 ELSE 0 END) AS poor_critical_assets,
        SUM(CASE WHEN flood_risk_zone = 'High' THEN 1 ELSE 0 END) AS high_flood_risk_assets,
        ROUND(SUM(maintenance_spend_aud), 2) AS maintenance_spend_aud,
        ROUND(SUM(reactive_cost_aud), 2) AS reactive_cost_aud,
        ROUND(SUM(capital_pipeline_aud), 2) AS capital_pipeline_aud
    FROM asset_base
    GROUP BY suburb
    ORDER BY poor_critical_assets DESC, reactive_cost_aud DESC
    """,
    "monthly_maintenance_trend.csv": """
    WITH work_cost AS (
        SELECT
            substr(m.work_date, 1, 7) AS work_month,
            m.planned_unplanned,
            COUNT(*) AS work_orders,
            SUM(COALESCE(c.amount_aud, 0)) AS total_cost_aud
        FROM maintenance m
        LEFT JOIN cost c
            ON m.work_order_id = c.linked_work_order_id
        GROUP BY substr(m.work_date, 1, 7), m.planned_unplanned
    )
    SELECT
        work_month,
        SUM(work_orders) AS total_work_orders,
        ROUND(SUM(total_cost_aud), 2) AS total_cost_aud,
        ROUND(100.0 * SUM(CASE WHEN planned_unplanned = 'Unplanned' THEN total_cost_aud ELSE 0 END) / NULLIF(SUM(total_cost_aud), 0), 2) AS reactive_share_pct
    FROM work_cost
    GROUP BY work_month
    ORDER BY work_month
    """,
    "annual_condition_trend.csv": """
    SELECT
        substr(inspection_date, 1, 4) AS inspection_year,
        asset_type,
        ROUND(AVG(condition_score), 2) AS avg_condition_score,
        SUM(CASE WHEN condition_score < 2.5 THEN 1 ELSE 0 END) AS poor_critical_assets
    FROM condition c
    JOIN assets a
        ON c.asset_id = a.asset_id
    GROUP BY substr(inspection_date, 1, 4), asset_type
    ORDER BY inspection_year, asset_type
    """,
    "renewal_priority_register.csv": BASE_CTES
    + """
    SELECT
        asset_id,
        asset_name,
        asset_type,
        suburb,
        criticality,
        flood_risk_zone,
        latest_condition_score,
        latest_condition_state,
        latest_risk_rating,
        age_years,
        life_consumed_pct,
        ROUND(reactive_cost_24m_aud, 2) AS reactive_cost_24m_aud,
        ROUND(capital_pipeline_aud, 2) AS capital_pipeline_aud,
        ROUND(
            ((5.0 - latest_condition_score) * 24)
            + (CASE criticality WHEN 'Critical' THEN 18 WHEN 'High' THEN 11 ELSE 6 END)
            + (CASE flood_risk_zone WHEN 'High' THEN 12 WHEN 'Moderate' THEN 6 ELSE 1 END)
            + (CASE WHEN life_consumed_pct > 100 THEN 18 ELSE life_consumed_pct / 8 END)
            + (reactive_cost_24m_aud / NULLIF(replacement_value_aud, 0) * 140),
            2
        ) AS priority_score,
        CASE
            WHEN latest_condition_score < 2.0 THEN 'Immediate renewal or major intervention'
            WHEN latest_condition_score < 2.5 THEN 'Prioritise in next capital works program'
            WHEN reactive_cost_24m_aud > 20000 THEN 'Review maintenance strategy and scope renewal'
            ELSE 'Monitor through annual inspection cycle'
        END AS recommendation
    FROM asset_base
    ORDER BY priority_score DESC, capital_pipeline_aud DESC
    LIMIT 25
    """,
}


def load_csv_to_sqlite(connection: sqlite3.Connection, table_name: str, csv_path: Path, columns: list[str]) -> None:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [tuple(row[column] for column in columns) for row in reader]

    placeholders = ", ".join(["?"] * len(columns))
    connection.executemany(
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
        rows,
    )


def write_query_results(connection: sqlite3.Connection, file_name: str, query: str) -> None:
    cursor = connection.execute(query)
    headers = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    output_path = OUTPUT_DIR / file_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> None:
    connection = sqlite3.connect(":memory:")

    for table_name, (ddl, columns) in TABLE_DEFINITIONS.items():
        connection.execute(ddl)
        load_csv_to_sqlite(connection, table_name, RAW_DIR / f"{table_name}.csv", columns)

    for file_name, query in OUTPUT_QUERIES.items():
        write_query_results(connection, file_name, query)

    print(f"Wrote {len(OUTPUT_QUERIES)} dashboard output files to {OUTPUT_DIR}.")


if __name__ == "__main__":
    main()
