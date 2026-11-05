"""HTTP server and REST API for ClientPhalanx studio and client portal."""

import http.server
import json
import os
import socketserver
import urllib.parse
from .portal import FreelancePortal

STATIC_DIR = os.path.join(os.path.dirname(__file__), "web")


class ClientPhalanxHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler serving portal endpoints and freelancer console."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    @property
    def portal(self) -> FreelancePortal:
        if not hasattr(self.server, "portal"):
            self.server.portal = FreelancePortal()
        return self.server.portal

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/status":
            self.send_json(200, {"status": "active", "service": "ClientPhalanx"})
            return

        elif parsed.path == "/api/dashboard":
            summary = self.portal.get_dashboard_summary()
            self.send_json(200, summary)
            return

        elif parsed.path.startswith("/api/portal/"):
            token = parsed.path.split("/api/portal/")[1].strip()
            view = self.portal.get_portal_view(token)
            if view:
                self.send_json(200, view)
            else:
                self.send_json(404, {"error": "Invalid portal token"})
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"

        try:
            data = json.loads(post_body)
        except Exception:
            data = {}

        if parsed.path == "/api/clients":
            name = data.get("name", "")
            company = data.get("company", "")
            email = data.get("email", "")
            rate = float(data.get("hourly_rate", 85.0))
            currency = data.get("currency", "USD")
            if not name:
                self.send_json(400, {"error": "Client name required"})
                return
            c = self.portal.add_client(name, company, email, rate, currency)
            self.send_json(200, c)
            return

        elif parsed.path == "/api/projects":
            cid = data.get("client_id", "")
            title = data.get("title", "")
            budget = float(data.get("budget", 0.0))
            deadline = data.get("deadline", "")
            description = data.get("description", "")
            if not cid or not title:
                self.send_json(400, {"error": "Client and project title required"})
                return
            p = self.portal.add_project(cid, title, budget, deadline, description)
            self.send_json(200, p)
            return

        elif parsed.path == "/api/milestones":
            pid = data.get("project_id", "")
            name = data.get("name", "")
            amount = float(data.get("amount", 0.0))
            due = data.get("due_date", "")
            ms = self.portal.add_milestone(pid, name, amount, due)
            if ms:
                self.send_json(200, ms)
            else:
                self.send_json(404, {"error": "Project not found"})
            return

        elif parsed.path == "/api/milestones/toggle":
            pid = data.get("project_id", "")
            mid = data.get("milestone_id", "")
            res = self.portal.toggle_milestone(pid, mid)
            if res is not None:
                self.send_json(200, {"completed": res})
            else:
                self.send_json(404, {"error": "Milestone not found"})
            return

        elif parsed.path == "/api/invoices":
            cid = data.get("client_id", "")
            items = data.get("items", [])
            due_days = int(data.get("due_days", 14))
            tax = float(data.get("tax_percent", 0.0))
            notes = data.get("notes", "")
            if not cid or not items:
                self.send_json(400, {"error": "Client ID and line items required"})
                return
            try:
                inv = self.portal.create_invoice(cid, items, due_days, tax, notes)
                self.send_json(200, inv)
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        elif parsed.path == "/api/invoices/status":
            inv_id = data.get("id", "")
            status = data.get("status", "PAID")
            ok = self.portal.set_invoice_status(inv_id, status)
            if ok:
                self.send_json(200, {"id": inv_id, "status": status})
            else:
                self.send_json(404, {"error": "Invoice not found"})
            return

        self.send_json(404, {"error": "Endpoint not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/clients/"):
            cid = parsed.path.split("/api/clients/")[1].strip()
            ok = self.portal.delete_client(cid)
            if ok:
                self.send_json(200, {"status": "deleted", "id": cid})
            else:
                self.send_json(404, {"error": "Client not found"})
            return
        elif parsed.path.startswith("/api/invoices/"):
            inv_id = parsed.path.split("/api/invoices/")[1].strip()
            ok = self.portal.delete_invoice(inv_id)
            if ok:
                self.send_json(200, {"status": "deleted", "id": inv_id})
            else:
                self.send_json(404, {"error": "Invoice not found"})
            return

        self.send_json(404, {"error": "Endpoint not found"})

    def send_json(self, status: int, payload: Any):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def log_message(self, format, *args):
        pass


def run_server(port: int = 7093, host: str = "127.0.0.1", file_path: str = None):
    """Starts the ClientPhalanx portal web server."""
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer((host, port), ClientPhalanxHandler)
    server.portal = FreelancePortal(file_path)
    print(f"[*] ClientPhalanx Portal active at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping ClientPhalanx server.")
