"""Command-line interface for ClientPhalanx."""

import argparse
import json
import sys
from . import __version__
from .portal import FreelancePortal
from .server import run_server


def main():
    parser = argparse.ArgumentParser(
        prog="clientphalanx",
        description="ClientPhalanx: Self-Hosted Freelancer Client Portal & Invoicing Engine"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--data", help="Custom path to data.json storage")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # summary
    subparsers.add_parser("summary", help="Display business financial metrics and active counts")

    # add-client
    add_c = subparsers.add_parser("add-client", help="Register a new client profile")
    add_c.add_argument("name", help="Client name")
    add_c.add_argument("--company", default="", help="Client organization/company")
    add_c.add_argument("--email", default="", help="Billing email")
    add_c.add_argument("--rate", type=float, default=85.0, help="Default hourly rate (default: 85.0)")
    add_c.add_argument("--currency", default="USD", help="Billing currency (default: USD)")

    # invoice
    inv_p = subparsers.add_parser("invoice", help="Generate an itemized invoice")
    inv_p.add_argument("client_id", help="Client ID or client exact name")
    inv_p.add_argument("description", help="Service line item description")
    inv_p.add_argument("hours", type=float, help="Billable hours / quantity")
    inv_p.add_argument("--rate", type=float, default=None, help="Custom hourly rate (defaults to client rate)")
    inv_p.add_argument("--tax", type=float, default=0.0, help="Sales tax percentage (default: 0.0)")

    # mark-paid
    paid_p = subparsers.add_parser("mark-paid", help="Mark an invoice as settled / PAID")
    paid_p.add_argument("invoice_id", help="Invoice ID (e.g. INV-2026-001)")

    # list-invoices
    subparsers.add_parser("list-invoices", help="List all generated invoices")

    # serve
    serve_p = subparsers.add_parser("serve", help="Launch the web-based Client Portal & Studio")
    serve_p.add_argument("--port", type=int, default=7093, help="Web server port (default: 7093)")
    serve_p.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")

    args = parser.parse_args()

    if args.command == "serve":
        run_server(port=args.port, host=args.host, file_path=args.data)
        return

    portal = FreelancePortal(args.data)

    if args.command == "add-client":
        c = portal.add_client(args.name, args.company, args.email, args.rate, args.currency)
        print(f"✓ Created client: {c['name']} (ID: {c['id']}) - ${c['hourly_rate']}/h")
        print(f"  Portal token link: /api/portal/{c['portal_token']}")
        return

    if args.command == "invoice":
        # Resolve client ID if name given
        target_id = args.client_id
        for c in portal.data["clients"]:
            if c["name"].lower() == args.client_id.lower() or c["id"] == args.client_id:
                target_id = c["id"]
                break

        item = {"description": args.description, "hours": args.hours}
        if args.rate is not None:
            item["rate"] = args.rate

        try:
            inv = portal.create_invoice(target_id, [item], tax_percent=args.tax)
            print(f"✓ Invoice Generated: {inv['id']} for {inv['client_company'] or inv['client_name']}")
            print(f"  Total: ${inv['total']:.2f} {inv['currency']} (Due: {inv['due_date']})")
        except Exception as e:
            print(f"✗ Failed to create invoice: {e}")
        return

    if args.command == "mark-paid":
        ok = portal.set_invoice_status(args.invoice_id, "PAID")
        if ok:
            print(f"✓ Invoice {args.invoice_id} marked as PAID.")
        else:
            print(f"✗ Invoice {args.invoice_id} not found.")
        return

    if args.command == "list-invoices":
        invoices = portal.data["invoices"]
        bold = "\033[1m"
        emerald = "\033[92m"
        reset = "\033[0m"

        print(f"\n{bold}{emerald}=== ClientPhalanx Invoice Directory ==={reset}\n")
        if not invoices:
            print("No invoices generated yet.")
        else:
            for inv in invoices:
                status_color = "\033[92m" if inv["status"] == "PAID" else "\033[93m"
                print(f"• {bold}{inv['id']}{reset} | {inv['client_company'] or inv['client_name']} | ${inv['total']:.2f} | {status_color}{inv['status']}{reset} (Due: {inv['due_date']})")
        print("")
        return

    if args.command == "summary":
        summary = portal.get_dashboard_summary()
        m = summary["metrics"]
        bold = "\033[1m"
        emerald = "\033[92m"
        reset = "\033[0m"

        print(f"\n{bold}{emerald}=== ClientPhalanx Business Overview ==={reset}")
        print(f"Gross Invoiced:    ${m['total_invoiced']:,.2f}")
        print(f"Collected Revenue: ${m['total_paid']:,.2f}")
        print(f"Outstanding Due:   ${m['total_outstanding']:,.2f}")
        print(f"Active Clients:    {m['active_clients']}")
        print(f"Active Projects:   {m['active_projects']}\n")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
