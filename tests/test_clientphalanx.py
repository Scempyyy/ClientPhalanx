"""Unit tests for ClientPhalanx client portal, invoicing, and revenue tracking."""

import os
import shutil
import tempfile
import unittest
from clientphalanx.portal import FreelancePortal


class TestClientPhalanx(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "data.json")
        self.portal = FreelancePortal(file_path=self.data_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_client_crud(self):
        c = self.portal.add_client("Alice Smith", company="AliceTech", hourly_rate=100.0)
        self.assertEqual(len(self.portal.data["clients"]), 1)
        self.assertEqual(c["hourly_rate"], 100.0)
        self.assertTrue(len(c["portal_token"]) > 10)

        retrieved = self.portal.get_client(c["id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Alice Smith")

    def test_invoice_math_and_totals(self):
        c = self.portal.add_client("Bob", hourly_rate=100.0)
        items = [
            {"description": "Backend API", "hours": 10, "rate": 100.0},
            {"description": "Frontend UI", "hours": 5, "rate": 100.0}
        ]
        # subtotal: 1500. Tax: 10% -> 150. Total: 1650
        inv = self.portal.create_invoice(c["id"], items, due_days=14, tax_percent=10.0)
        self.assertEqual(inv["subtotal"], 1500.0)
        self.assertEqual(inv["tax_amount"], 150.0)
        self.assertEqual(inv["total"], 1650.0)
        self.assertEqual(inv["status"], "SENT")

    def test_metrics_aggregation(self):
        c = self.portal.add_client("Charlie", hourly_rate=50.0)
        inv1 = self.portal.create_invoice(c["id"], [{"description": "Work 1", "hours": 10, "rate": 50.0}]) # $500
        inv2 = self.portal.create_invoice(c["id"], [{"description": "Work 2", "hours": 20, "rate": 50.0}]) # $1000

        self.portal.set_invoice_status(inv1["id"], "PAID")

        summary = self.portal.get_dashboard_summary()
        m = summary["metrics"]
        self.assertEqual(m["total_invoiced"], 1500.0)
        self.assertEqual(m["total_paid"], 500.0)
        self.assertEqual(m["total_outstanding"], 1000.0)

    def test_client_portal_view(self):
        c = self.portal.add_client("Dave", hourly_rate=80.0)
        self.portal.add_project(c["id"], "Mobile App", budget=3000.0)
        self.portal.create_invoice(c["id"], [{"description": "Sprint 1", "hours": 10, "rate": 80.0}])

        view = self.portal.get_portal_view(c["portal_token"])
        self.assertIsNotNone(view)
        self.assertEqual(view["client"]["name"], "Dave")
        self.assertEqual(len(view["projects"]), 1)
        self.assertEqual(len(view["invoices"]), 1)


if __name__ == "__main__":
    unittest.main()
