#!/usr/bin/env python3
"""Generate relational-style CSV data for an asset insights portfolio project."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
SEED = 42
TODAY = date(2026, 3, 24)


@dataclass(frozen=True)
class AssetTypeConfig:
    count: int
    life_range: tuple[int, int]
    replacement_range: tuple[int, int]
    department: str
    maintenance_rate: float


ASSET_TYPES: dict[str, AssetTypeConfig] = {
    "Road Segment": AssetTypeConfig(28, (35, 55), (280_000, 1_400_000), "Works and Infrastructure", 1.30),
    "Footpath": AssetTypeConfig(22, (25, 40), (90_000, 420_000), "Works and Infrastructure", 0.95),
    "Drainage Line": AssetTypeConfig(20, (40, 70), (180_000, 920_000), "Infrastructure Services", 1.15),
    "Bridge": AssetTypeConfig(12, (60, 100), (1_400_000, 8_200_000), "Structures and Assets", 1.45),
    "Park Facility": AssetTypeConfig(18, (15, 30), (45_000, 260_000), "Parks and Recreation", 0.85),
    "Community Building": AssetTypeConfig(14, (35, 60), (850_000, 5_600_000), "Buildings and Facilities", 1.10),
}

SUBURBS = [
    {"suburb": "Ipswich Central", "ward": "Central", "precinct": "Urban Core", "lat": -27.6140, "lon": 152.7580, "flood_bias": 0.62},
    {"suburb": "Goodna", "ward": "East", "precinct": "Riverside", "lat": -27.6108, "lon": 152.8980, "flood_bias": 0.72},
    {"suburb": "Redbank Plains", "ward": "East", "precinct": "Growth Corridor", "lat": -27.6464, "lon": 152.8599, "flood_bias": 0.36},
    {"suburb": "Springfield", "ward": "South", "precinct": "Growth Corridor", "lat": -27.6549, "lon": 152.9022, "flood_bias": 0.25},
    {"suburb": "Ripley", "ward": "South", "precinct": "Development Front", "lat": -27.7293, "lon": 152.8240, "flood_bias": 0.21},
    {"suburb": "Yamanto", "ward": "West", "precinct": "Industrial Fringe", "lat": -27.6600, "lon": 152.7394, "flood_bias": 0.33},
    {"suburb": "Rosewood", "ward": "Rural", "precinct": "Western Rural", "lat": -27.6333, "lon": 152.5890, "flood_bias": 0.29},
    {"suburb": "Brassall", "ward": "West", "precinct": "Established Suburbs", "lat": -27.5979, "lon": 152.7477, "flood_bias": 0.41},
]

INSPECTORS = ["A. Singh", "J. Williams", "M. Tran", "P. O'Connor", "R. Chen"]
DEFECT_CATEGORIES = {
    "Road Segment": ["Pavement cracking", "Shoulder failure", "Surface rutting"],
    "Footpath": ["Trip hazard", "Concrete cracking", "Tree root uplift"],
    "Drainage Line": ["Blockage", "Pipe settlement", "Inlet damage"],
    "Bridge": ["Expansion joint wear", "Concrete spalling", "Guardrail damage"],
    "Park Facility": ["Playground wear", "Shelter corrosion", "Lighting fault"],
    "Community Building": ["Roof leak", "HVAC issue", "Accessibility defect"],
}


def random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def fiscal_year(dt: date) -> str:
    if dt.month >= 7:
        return f"FY{dt.year + 1}"
    return f"FY{dt.year}"


def condition_state(score: float) -> str:
    if score >= 4.5:
        return "Excellent"
    if score >= 3.5:
        return "Good"
    if score >= 2.5:
        return "Fair"
    if score >= 1.5:
        return "Poor"
    return "Critical"


def risk_rating(score: float, criticality: str, flood_zone: str) -> str:
    critical_boost = {"Medium": 0.0, "High": 0.35, "Critical": 0.65}[criticality]
    flood_boost = {"Low": 0.0, "Moderate": 0.2, "High": 0.45}[flood_zone]
    risk_index = (5.0 - score) + critical_boost + flood_boost
    if risk_index >= 4.0:
        return "Critical"
    if risk_index >= 2.9:
        return "High"
    if risk_index >= 1.8:
        return "Moderate"
    return "Low"


def choose_flood_zone(rng: random.Random, suburb_bias: float, asset_type: str) -> str:
    type_adjustment = 0.0
    if asset_type in {"Bridge", "Drainage Line"}:
        type_adjustment = 0.12
    score = suburb_bias + type_adjustment + rng.uniform(-0.12, 0.12)
    if score >= 0.68:
        return "High"
    if score >= 0.38:
        return "Moderate"
    return "Low"


def determine_criticality(asset_type: str, suburb: str) -> str:
    if asset_type in {"Bridge", "Community Building"}:
        return "Critical"
    if asset_type in {"Road Segment", "Drainage Line"} and suburb in {"Ipswich Central", "Goodna", "Springfield"}:
        return "High"
    return "Medium"


def latest_score_for_asset(
    *,
    install_date: date,
    expected_life: int,
    asset_type: str,
    flood_zone: str,
    criticality: str,
    rng: random.Random,
) -> float:
    age_years = (TODAY - install_date).days / 365.25
    age_ratio = age_years / expected_life
    type_penalty = {
        "Road Segment": 0.30,
        "Footpath": 0.20,
        "Drainage Line": 0.28,
        "Bridge": 0.35,
        "Park Facility": 0.16,
        "Community Building": 0.22,
    }[asset_type]
    flood_penalty = {"Low": 0.0, "Moderate": 0.25, "High": 0.55}[flood_zone]
    criticality_penalty = {"Medium": 0.0, "High": 0.12, "Critical": 0.18}[criticality]
    base_score = 5.1 - (age_ratio * 3.8) - type_penalty - flood_penalty - criticality_penalty + rng.uniform(-0.28, 0.22)
    return max(1.0, min(5.0, round(base_score, 1)))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)

    assets: list[dict[str, object]] = []
    locations: list[dict[str, object]] = []
    conditions: list[dict[str, object]] = []
    maintenance_rows: list[dict[str, object]] = []
    cost_rows: list[dict[str, object]] = []

    asset_number = 1
    inspection_number = 1
    work_order_number = 1
    cost_number = 1

    for asset_type, config in ASSET_TYPES.items():
        for type_sequence in range(1, config.count + 1):
            suburb_meta = rng.choices(
                SUBURBS,
                weights=[14, 11, 13, 12, 10, 9, 7, 10],
                k=1,
            )[0]
            install_dt = random_date(rng, date(1986, 1, 1), date(2022, 6, 30))
            expected_life = rng.randint(*config.life_range)
            replacement_value = round(rng.uniform(*config.replacement_range), 2)
            flood_zone = choose_flood_zone(rng, suburb_meta["flood_bias"], asset_type)
            criticality = determine_criticality(asset_type, suburb_meta["suburb"])
            asset_id = f"AST-{asset_number:04d}"
            asset_name = f"{asset_type} - {suburb_meta['suburb']} - {type_sequence:02d}"

            assets.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "asset_type": asset_type,
                    "install_date": install_dt.isoformat(),
                    "expected_life_years": expected_life,
                    "replacement_value_aud": f"{replacement_value:.2f}",
                    "criticality": criticality,
                    "owner_department": config.department,
                    "status": "Active",
                }
            )

            locations.append(
                {
                    "location_id": f"LOC-{asset_number:04d}",
                    "asset_id": asset_id,
                    "suburb": suburb_meta["suburb"],
                    "ward": suburb_meta["ward"],
                    "precinct": suburb_meta["precinct"],
                    "latitude": f"{suburb_meta['lat'] + rng.uniform(-0.018, 0.018):.6f}",
                    "longitude": f"{suburb_meta['lon'] + rng.uniform(-0.018, 0.018):.6f}",
                    "flood_risk_zone": flood_zone,
                }
            )

            current_score = latest_score_for_asset(
                install_date=install_dt,
                expected_life=expected_life,
                asset_type=asset_type,
                flood_zone=flood_zone,
                criticality=criticality,
                rng=rng,
            )

            yearly_scores: dict[int, float] = {}
            for inspection_year in range(2022, 2026):
                prior_year_bonus = (2025 - inspection_year) * rng.uniform(0.08, 0.24)
                score = max(1.0, min(5.0, round(current_score + prior_year_bonus + rng.uniform(-0.18, 0.12), 1)))
                yearly_scores[inspection_year] = score
                conditions.append(
                    {
                        "inspection_id": f"INSP-{inspection_number:05d}",
                        "asset_id": asset_id,
                        "inspection_date": random_date(
                            rng,
                            date(inspection_year, 2, 1),
                            date(inspection_year, 11, 30),
                        ).isoformat(),
                        "condition_score": f"{score:.1f}",
                        "condition_state": condition_state(score),
                        "defect_count": max(0, int(round((5.2 - score) * rng.uniform(1.8, 4.5)))),
                        "risk_rating": risk_rating(score, criticality, flood_zone),
                        "inspector": rng.choice(INSPECTORS),
                    }
                )
                inspection_number += 1

            latest_condition = yearly_scores[2025]
            maintenance_factor = config.maintenance_rate + max(0.0, (3.4 - latest_condition) * 0.55)
            planned_orders = rng.randint(1, 3)
            reactive_orders = rng.randint(0, 2 if latest_condition >= 2.6 else 4)
            total_orders = max(1, int(round((planned_orders + reactive_orders) * maintenance_factor / 1.4)))

            work_dates = sorted(
                random_date(rng, date(2023, 1, 1), date(2025, 12, 20))
                for _ in range(total_orders)
            )

            for work_dt in work_dates:
                reactive_probability = max(0.18, min(0.78, 0.22 + (3.0 - latest_condition) * 0.18))
                is_reactive = rng.random() < reactive_probability
                if latest_condition <= 2.0 and rng.random() < 0.22:
                    maintenance_type = "Emergency Repair"
                    planned_flag = "Unplanned"
                    priority = "Urgent"
                elif is_reactive:
                    maintenance_type = rng.choice(["Reactive Repair", "Defect Rectification"])
                    planned_flag = "Unplanned"
                    priority = rng.choice(["High", "Urgent"] if latest_condition < 2.5 else ["Medium", "High"])
                else:
                    maintenance_type = rng.choice(["Preventive Maintenance", "Routine Servicing", "Minor Renewal"])
                    planned_flag = "Planned"
                    priority = rng.choice(["Low", "Medium", "High"])

                labor_hours = round(
                    rng.uniform(3.0, 18.0)
                    * (1.2 if maintenance_type in {"Emergency Repair", "Minor Renewal"} else 1.0)
                    * (1.3 if asset_type in {"Bridge", "Community Building"} else 1.0),
                    1,
                )
                contractor_used = "Yes" if asset_type in {"Bridge", "Community Building"} or labor_hours > 16 else "No"
                work_order_id = f"WO-{work_order_number:05d}"

                maintenance_rows.append(
                    {
                        "work_order_id": work_order_id,
                        "asset_id": asset_id,
                        "work_date": work_dt.isoformat(),
                        "maintenance_type": maintenance_type,
                        "priority": priority,
                        "planned_unplanned": planned_flag,
                        "status": "Completed",
                        "labor_hours": f"{labor_hours:.1f}",
                        "contractor_used": contractor_used,
                        "defect_category": rng.choice(DEFECT_CATEGORIES[asset_type]),
                    }
                )

                labor_rate = 110 if contractor_used == "No" else 155
                material_multiplier = {
                    "Preventive Maintenance": 0.55,
                    "Routine Servicing": 0.40,
                    "Reactive Repair": 1.00,
                    "Defect Rectification": 0.95,
                    "Emergency Repair": 1.65,
                    "Minor Renewal": 2.25,
                }[maintenance_type]
                amount = (labor_hours * labor_rate) + rng.uniform(500, 2_400) * material_multiplier
                if asset_type == "Bridge":
                    amount *= 1.55
                elif asset_type == "Community Building":
                    amount *= 1.35
                elif asset_type == "Drainage Line" and maintenance_type in {"Emergency Repair", "Minor Renewal"}:
                    amount *= 1.25

                cost_rows.append(
                    {
                        "cost_id": f"COST-{cost_number:05d}",
                        "asset_id": asset_id,
                        "cost_date": work_dt.isoformat(),
                        "cost_type": "Operational" if maintenance_type not in {"Minor Renewal", "Emergency Repair"} else "Capital",
                        "amount_aud": f"{amount:.2f}",
                        "funding_source": "Operating Budget" if planned_flag == "Planned" else "Reactive Maintenance Reserve",
                        "linked_work_order_id": work_order_id,
                        "fiscal_year": fiscal_year(work_dt),
                    }
                )
                work_order_number += 1
                cost_number += 1

            if latest_condition <= 2.2 or (
                criticality == "Critical" and latest_condition <= 2.6 and rng.random() < 0.55
            ):
                renewal_dt = random_date(rng, date(2025, 7, 1), date(2026, 3, 15))
                renewal_amount = replacement_value * rng.uniform(0.22, 0.58)
                cost_rows.append(
                    {
                        "cost_id": f"COST-{cost_number:05d}",
                        "asset_id": asset_id,
                        "cost_date": renewal_dt.isoformat(),
                        "cost_type": "Capital Planned",
                        "amount_aud": f"{renewal_amount:.2f}",
                        "funding_source": "Renewal Program",
                        "linked_work_order_id": "",
                        "fiscal_year": fiscal_year(renewal_dt),
                    }
                )
                cost_number += 1

            asset_number += 1

    write_csv(
        RAW_DIR / "assets.csv",
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
        assets,
    )
    write_csv(
        RAW_DIR / "locations.csv",
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
        locations,
    )
    write_csv(
        RAW_DIR / "condition.csv",
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
        conditions,
    )
    write_csv(
        RAW_DIR / "maintenance.csv",
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
        maintenance_rows,
    )
    write_csv(
        RAW_DIR / "cost.csv",
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
        cost_rows,
    )

    print(
        "Generated "
        f"{len(assets)} assets, {len(locations)} locations, {len(conditions)} inspections, "
        f"{len(maintenance_rows)} maintenance records, and {len(cost_rows)} cost records."
    )


if __name__ == "__main__":
    main()
