# Asset Insights Dashboard Portfolio Project

Practical portfolio project for an Asset Data Analyst style role, focused on local government infrastructure planning. The project simulates a council asset portfolio and produces reusable SQL analysis, Python preparation scripts, and dashboard-ready outputs for backlog, condition, maintenance, and renewal decisions.

## Recruiter Snapshot

- Demonstrates SQL-based data cleaning, joins, KPI analysis, and trend analysis.
- Produces dashboard-ready outputs for Power BI, Tableau, or Excel.
- Framed around realistic local-government and infrastructure analytics work.
- Shows both technical data preparation and business-facing insight generation.

## Project Scope

This project models a council-owned asset portfolio across:

- Road segments
- Footpaths
- Drainage lines
- Bridges
- Park facilities
- Community buildings

The dataset is relational in style and split into separate CSV tables for:

- `assets`
- `locations`
- `condition`
- `maintenance`
- `cost`

Generated sample data includes:

- 114 assets
- 456 inspection / condition records
- 467 maintenance work orders
- 510 cost transactions

## Why This Project Works For A Portfolio

It reflects the kind of work an asset analyst might do in a council or infrastructure planning team:

- combine asset master data with inspection and work order history
- clean and join multiple operational datasets
- calculate condition, risk, spend, and renewal KPIs
- identify where backlog is driven by service volume versus capital value
- prepare flat outputs for Power BI, Tableau, or Excel reporting

## Folder Structure

```text
asset-insights-dashboard/
├── data/raw/                     # Relational-style source CSVs
├── docs/
│   ├── data-dictionary.md
│   └── resume-bullets.md
├── outputs/dashboard/            # Dashboard-ready summary CSVs
├── scripts/
│   ├── generate_sample_data.py
│   └── prepare_dashboard_outputs.py
└── sql/
    ├── 01_cleaning.sql
    ├── 02_joins.sql
    ├── 03_kpi_queries.sql
    └── 04_trend_analysis.sql
```

## KPI Framework

The dashboard outputs are built around practical asset planning measures:

- `Average latest condition score`: current asset health on a 1 to 5 scale
- `Poor or critical assets`: assets with a latest condition score below 2.5
- `Assets past 80% of expected life`: age-based renewal pressure
- `Reactive maintenance share (%)`: share of completed maintenance spend tied to unplanned work
- `Planned capital pipeline (AUD)`: forward renewal need estimated from poor-condition and high-criticality assets

## Headline Results

Current portfolio position from `outputs/dashboard/kpi_summary.csv`:

- Total replacement value: `AUD 150.15M`
- Average latest condition score: `2.76 / 5`
- Poor or critical assets: `46 of 114` assets (`40.35%`)
- Assets past 80% of expected life: `18`
- Total maintenance spend captured in work orders: `AUD 1.68M`
- Reactive maintenance share: `34.45%`
- Planned capital pipeline: `AUD 21.92M`

## Key Findings

### 1. Backlog pressure is broad, but it is not uniform

Roads, footpaths, and drainage drive the largest backlog by asset count:

- Road segments: `12` poor / critical assets
- Footpaths: `11`
- Drainage lines: `10`

Park facilities have the weakest average condition score at `2.32`, which makes them a strong candidate for targeted service-level intervention even though their capital values are lower than bridges or buildings.

### 2. Count-based risk and value-based risk are different problems

Community buildings and bridges are not the worst asset classes by average condition, but they dominate the forward renewal program by value:

- Community buildings: `AUD 9.47M` capital pipeline
- Bridges: `AUD 5.20M`
- Road segments: `AUD 4.00M`

This is a realistic council planning pattern: roads and footpaths create visible service backlog, while a smaller number of high-value structures can dominate long-term capital budgeting.

### 3. Place matters

Ipswich Central is the highest-risk geography in the sample portfolio:

- `23` assets
- `12` poor / critical assets
- `8` assets in high flood-risk zones
- `AUD 9.31M` in planned capital pipeline

Brassall also stands out with the lowest suburb-level average condition score at `2.26`.

### 4. Deterioration is visible across every major asset class

Average condition declined between 2022 and 2025 for all asset classes:

- Footpaths: `3.07` to `2.53` (`-0.54`)
- Community buildings: `3.75` to `3.24` (`-0.51`)
- Drainage lines: `3.26` to `2.79` (`-0.47`)
- Park facilities: `2.77` to `2.32` (`-0.45`)
- Road segments: `3.20` to `2.76` (`-0.44`)
- Bridges: `3.53` to `3.18` (`-0.35`)

That pattern supports a planning narrative around growing renewal pressure rather than isolated defects.

### 5. Reactive spend is material enough to monitor monthly

Unplanned work represents `34.45%` of maintenance spend overall, with several monthly peaks above `50%` in the generated trend output. That is a reasonable trigger for a council asset team to investigate whether inspection frequency, preventive maintenance timing, or renewal timing needs adjustment.

## Recommendations

### 1. Split the renewal response into two programs

- Service backlog program: roads, footpaths, parks, and drainage
- High-value capital program: community buildings and bridges

This prevents high-volume service issues from being hidden behind a small number of expensive assets.

### 2. Prioritise the top renewal register for near-term capital planning

The renewal priority register highlights assets that combine:

- poor condition
- high life consumed percentage
- flood exposure
- high criticality
- elevated recent reactive spend

The top-ranked assets are dominated by park facilities and footpaths in Yamanto, Brassall, Goodna, and Ipswich Central.

### 3. Use place-based resilience planning in flood-exposed areas

Ipswich Central and Goodna should be reviewed for:

- drainage capacity issues
- flood-sensitive renewal timing
- higher inspection frequency on exposed assets

### 4. Track reactive share as an operating KPI

If reactive maintenance continues to sit above roughly `30% to 35%`, the council should review whether preventive maintenance coverage is too low or whether assets have moved beyond economical maintenance into renewal territory.

## How To Run

The project uses only the Python standard library.

Generate the raw relational CSVs:

```bash
python3 scripts/generate_sample_data.py
```

Prepare dashboard-ready outputs:

```bash
python3 scripts/prepare_dashboard_outputs.py
```

## SQL Usage

The SQL files are written in a SQLite-friendly style and can also be adapted easily for DuckDB or similar tools after importing the CSVs as tables.

- `sql/01_cleaning.sql`: trimming, type casting, standardisation
- `sql/02_joins.sql`: analyst-ready joined asset base
- `sql/03_kpi_queries.sql`: executive and asset-type KPI queries
- `sql/04_trend_analysis.sql`: deterioration, maintenance, and place-based trend analysis

## Dashboard-Ready Outputs

The `outputs/dashboard/` folder includes:

- `kpi_summary.csv`
- `asset_type_summary.csv`
- `suburb_risk_summary.csv`
- `monthly_maintenance_trend.csv`
- `annual_condition_trend.csv`
- `renewal_priority_register.csv`

These can be loaded directly into Power BI, Tableau, or Excel as a lightweight reporting layer.

## Dashboard Visuals

Dashboard screenshots will be added after the reporting layer is visualised in Power BI or Excel. The current repository already includes dashboard-ready CSV outputs in `outputs/dashboard/`.

## Supporting Documentation

- Data dictionary: `docs/data-dictionary.md`
- Resume-ready bullet points: `docs/resume-bullets.md`

## Suggested Dashboard Pages

- Portfolio overview
- Asset class condition and backlog
- Geographic risk and flood exposure
- Maintenance trend and reactive share
- Renewal priority register
