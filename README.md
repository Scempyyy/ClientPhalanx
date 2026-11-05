# ClientPhalanx 💼🧾

[![CI](https://github.com/Scempyyy/ClientPhalanx/actions/workflows/ci.yml/badge.svg)](https://github.com/Scempyyy/ClientPhalanx/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://python.org)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](#)

> **Self-Hosted Freelancer Client Portal & Invoicing Engine.**  
> A lightweight, zero-cloud client operations workspace for solo software engineers, consultants, and agencies. Track deliverable milestones, generate clean itemized invoices, and share passwordless tokenized portals with clients.

---

## ⚡ Highlights

- **100% Self-Hosted & Private:** Zero third-party SaaS subscriptions, zero telemetry. All records persist in an open JSON format.
- **Itemized Invoice Generator:** Auto-calculates billable line items, customizable tax rates, net-14/30 payment terms, and status tracking (DRAFT, SENT, PAID).
- **Client Access Portals:** Provides unique, secure, read-only tokenized URLs (`/api/portal/<token>`) clients can visit to inspect invoices and project progress without creating accounts.
- **Project Milestone Tracker:** Tracks project deliverable statuses, sprint budgets, and completion percentages.
- **Zero Third-Party Dependencies:** 100% standard library Python 3 (`json`, `http.server`, `datetime`, `secrets`, `uuid`).
- **Dual Interface:** Full terminal CLI for automated invoicing and a sleek dark-mode web console.

---

## 🚀 Quick Start

### 1. Launch the Freelancer Studio
```bash
git clone https://github.com/Scempyyy/ClientPhalanx.git
cd ClientPhalanx
./clientphalanx.py serve --port 7093
```
Open [http://localhost:7093](http://localhost:7093) in your browser.

### 2. Manage Clients & Invoices via CLI
```bash
# Add a new client
./clientphalanx.py add-client "Acme Corp" --company "Acme Corp" --rate 120.0

# Generate an invoice
./clientphalanx.py invoice "Acme Corp" "Backend API refactoring" 20 --tax 5.0

# Mark invoice as settled
./clientphalanx.py mark-paid INV-2026-001
```

---

## 💻 CLI Commands

```bash
# Display revenue metrics (invoiced, collected, outstanding)
python3 clientphalanx.py summary

# List all generated invoices
python3 clientphalanx.py list-invoices

# Register new client
python3 clientphalanx.py add-client "Jane Doe" --company "FinTech Labs" --rate 150.0

# Launch web console on a custom port
python3 clientphalanx.py serve --port 8080 --host 0.0.0.0
```

---

## 🔬 Testing

Run the test suite:
```bash
python3 -m unittest discover tests -v
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details. Built by [Scempyyy](https://github.com/Scempyyy).
