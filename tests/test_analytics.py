"""Reconcile generated reporting outputs against independent source calculations."""
import csv
import sqlite3
import unittest
from collections import Counter
from pathlib import Path
from scripts.prepare_dashboard_outputs import TABLE_DEFINITIONS, OUTPUT_QUERIES, load_csv_to_sqlite

ROOT = Path(__file__).resolve().parents[1]

class AnalyticsContractTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.raw = {}
        for name, (ddl, columns) in TABLE_DEFINITIONS.items():
            self.db.execute(ddl)
            path = ROOT / "data/raw" / f"{name}.csv"
            with path.open(newline="") as handle:
                self.raw[name] = list(csv.DictReader(handle))
            load_csv_to_sqlite(self.db, name, path, columns)

    def test_source_keys_and_references_are_consistent(self):
        assets = {row["asset_id"] for row in self.raw["assets"]}
        work_orders = {row["work_order_id"] for row in self.raw["maintenance"]}
        for name, (_, columns) in TABLE_DEFINITIONS.items():
            ids = [row[columns[0]] for row in self.raw[name]]
            self.assertEqual(len(ids), len(set(ids)), name)
            self.assertTrue(all(row["asset_id"] in assets for row in self.raw[name]), name)
        self.assertTrue(all(not row["linked_work_order_id"] or row["linked_work_order_id"] in work_orders for row in self.raw["cost"]))

    def test_executive_totals_reconcile_to_source_data(self):
        metrics = {row[0]: row[1] for row in self.db.execute(OUTPUT_QUERIES["kpi_summary.csv"])}
        self.assertEqual(int(metrics["Total assets"]), len(self.raw["assets"]))
        total = sum(float(row["replacement_value_aud"]) for row in self.raw["assets"])
        self.assertAlmostEqual(float(metrics["Total replacement value (AUD)"]), total, places=2)
        latest = {}
        for row in sorted(self.raw["condition"], key=lambda row: row["inspection_date"]):
            latest[row["asset_id"]] = row
        poor = sum(float(row["condition_score"]) < 2.5 for row in latest.values())
        self.assertEqual(int(metrics["Poor or critical assets"]), poor)

    def test_monthly_work_order_counts_reconcile(self):
        expected = Counter(row["work_date"][:7] for row in self.raw["maintenance"])
        actual = {row[0]: row[1] for row in self.db.execute(OUTPUT_QUERIES["monthly_maintenance_trend.csv"])}
        self.assertEqual(actual, dict(expected))

    def test_asset_class_counts_do_not_multiply_in_joins(self):
        actual = {row[0]: row[1] for row in self.db.execute(OUTPUT_QUERIES["asset_type_summary.csv"])}
        self.assertEqual(actual, dict(Counter(row["asset_type"] for row in self.raw["assets"])))

    def test_committed_reports_match_current_queries(self):
        for filename, query in OUTPUT_QUERIES.items():
            with self.subTest(filename=filename):
                cursor = self.db.execute(query)
                expected = [[column[0] for column in cursor.description]]
                expected += [["" if value is None else str(value) for value in row] for row in cursor]
                with (ROOT / "outputs/dashboard" / filename).open(newline="") as handle:
                    self.assertEqual(list(csv.reader(handle)), expected)

if __name__ == "__main__":
    unittest.main()
