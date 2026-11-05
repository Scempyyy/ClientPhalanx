"""Data models, business logic, invoice calculations, and persistence for ClientPhalanx."""

import datetime
import json
import os
import secrets
import uuid
from typing import Dict, List, Any, Optional

DEFAULT_DATA_FILE = os.path.expanduser("~/.clientphalanx/data.json")


class FreelancePortal:
    """Self-contained freelancer business manager and client portal."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or DEFAULT_DATA_FILE
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.data: Dict[str, Any] = {
            "clients": [],
            "projects": [],
            "invoices": [],
            "profile": {
                "name": "Alex Mercer",
                "business_name": "Mercer Digital Systems",
                "email": "alex@mercer.dev",
                "payment_details": "Wire Transfer: Routing #123456789, Account #987654321"
            }
        }
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    # 1. Clients
    def add_client(self, name: str, company: str = "", email: str = "", hourly_rate: float = 85.0, currency: str = "USD") -> Dict[str, Any]:
        client = {
            "id": f"cli-{uuid.uuid4().hex[:6]}",
            "name": name.strip(),
            "company": company.strip() or name.strip(),
            "email": email.strip(),
            "hourly_rate": float(hourly_rate),
            "currency": currency.upper().strip(),
            "portal_token": secrets.token_urlsafe(16),
            "created_at": datetime.datetime.now().isoformat()
        }
        self.data["clients"].append(client)
        self.save()
        return client

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        for c in self.data["clients"]:
            if c["id"] == client_id:
                return c
        return None

    def delete_client(self, client_id: str) -> bool:
        init_len = len(self.data["clients"])
        self.data["clients"] = [c for c in self.data["clients"] if c["id"] != client_id]
        if len(self.data["clients"]) < init_len:
            self.save()
            return True
        return False

    # 2. Projects & Milestones
    def add_project(self, client_id: str, title: str, budget: float = 0.0, deadline: str = "", description: str = "") -> Dict[str, Any]:
        project = {
            "id": f"prj-{uuid.uuid4().hex[:6]}",
            "client_id": client_id,
            "title": title.strip(),
            "description": description.strip(),
            "budget": float(budget),
            "deadline": deadline.strip(),
            "status": "ACTIVE",
            "milestones": [],
            "created_at": datetime.datetime.now().isoformat()
        }
        self.data["projects"].append(project)
        self.save()
        return project

    def add_milestone(self, project_id: str, name: str, amount: float = 0.0, due_date: str = "") -> Optional[Dict[str, Any]]:
        for p in self.data["projects"]:
            if p["id"] == project_id:
                ms = {
                    "id": f"mls-{uuid.uuid4().hex[:4]}",
                    "name": name.strip(),
                    "amount": float(amount),
                    "due_date": due_date.strip(),
                    "completed": False
                }
                p["milestones"].append(ms)
                self.save()
                return ms
        return None

    def toggle_milestone(self, project_id: str, milestone_id: str) -> Optional[bool]:
        for p in self.data["projects"]:
            if p["id"] == project_id:
                for ms in p["milestones"]:
                    if ms["id"] == milestone_id:
                        ms["completed"] = not ms["completed"]
                        self.save()
                        return ms["completed"]
        return None

    # 3. Invoice Generator
    def create_invoice(self, client_id: str, items: List[Dict[str, Any]], due_days: int = 14, tax_percent: float = 0.0, notes: str = "") -> Dict[str, Any]:
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        inv_num = f"INV-{datetime.datetime.now().year}-{len(self.data['invoices']) + 1:03d}"
        issue_date = datetime.date.today().isoformat()
        due_date = (datetime.date.today() + datetime.timedelta(days=due_days)).isoformat()

        subtotal = 0.0
        calculated_items = []
        for it in items:
            desc = it.get("description", "Consulting & Development")
            hours = float(it.get("hours", 1.0))
            rate = float(it.get("rate", client.get("hourly_rate", 85.0)))
            total = round(hours * rate, 2)
            subtotal += total
            calculated_items.append({
                "description": desc,
                "hours": hours,
                "rate": rate,
                "total": total
            })

        tax_amount = round(subtotal * (tax_percent / 100.0), 2)
        grand_total = round(subtotal + tax_amount, 2)

        invoice = {
            "id": inv_num,
            "client_id": client_id,
            "client_name": client["name"],
            "client_company": client["company"],
            "currency": client.get("currency", "USD"),
            "issue_date": issue_date,
            "due_date": due_date,
            "status": "SENT",
            "items": calculated_items,
            "subtotal": subtotal,
            "tax_percent": tax_percent,
            "tax_amount": tax_amount,
            "total": grand_total,
            "notes": notes or "Thank you for your business. Payment due upon terms.",
            "created_at": datetime.datetime.now().isoformat()
        }

        self.data["invoices"].append(invoice)
        self.save()
        return invoice

    def set_invoice_status(self, invoice_id: str, status: str) -> bool:
        status = status.upper().strip()
        for inv in self.data["invoices"]:
            if inv["id"] == invoice_id:
                inv["status"] = status
                self.save()
                return True
        return False

    def delete_invoice(self, invoice_id: str) -> bool:
        init_len = len(self.data["invoices"])
        self.data["invoices"] = [inv for inv in self.data["invoices"] if inv["id"] != invoice_id]
        if len(self.data["invoices"]) < init_len:
            self.save()
            return True
        return False

    # 4. Analytics Summary
    def get_dashboard_summary(self) -> Dict[str, Any]:
        total_invoiced = sum(inv["total"] for inv in self.data["invoices"])
        total_paid = sum(inv["total"] for inv in self.data["invoices"] if inv.get("status") == "PAID")
        total_outstanding = sum(inv["total"] for inv in self.data["invoices"] if inv.get("status") != "PAID")

        # Map client details to projects
        client_map = {c["id"]: c for c in self.data["clients"]}
        enriched_projects = []
        for p in self.data["projects"]:
            c = client_map.get(p["client_id"], {})
            p_copy = dict(p)
            p_copy["client_name"] = c.get("name", "Unknown Client")
            p_copy["client_company"] = c.get("company", "")
            enriched_projects.append(p_copy)

        return {
            "metrics": {
                "total_invoiced": round(total_invoiced, 2),
                "total_paid": round(total_paid, 2),
                "total_outstanding": round(total_outstanding, 2),
                "active_clients": len(self.data["clients"]),
                "active_projects": sum(1 for p in self.data["projects"] if p.get("status") == "ACTIVE")
            },
            "clients": self.data["clients"],
            "projects": enriched_projects,
            "invoices": sorted(self.data["invoices"], key=lambda item: item["created_at"], reverse=True),
            "profile": self.data["profile"]
        }

    def get_portal_view(self, token: str) -> Optional[Dict[str, Any]]:
        """Returns read-only client portal view for a client matching portal_token."""
        client = None
        for c in self.data["clients"]:
            if c.get("portal_token") == token:
                client = c
                break
        if not client:
            return None

        client_projects = [p for p in self.data["projects"] if p["client_id"] == client["id"]]
        client_invoices = [inv for inv in self.data["invoices"] if inv["client_id"] == client["id"]]

        return {
            "client": client,
            "freelancer": self.data["profile"],
            "projects": client_projects,
            "invoices": client_invoices
        }
