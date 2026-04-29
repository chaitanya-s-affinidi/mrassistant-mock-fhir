"""CLI for MCP Client - call MCP tools interactively."""

import json
import os
from datetime import datetime

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import MCPClient, MCPError

app = typer.Typer(help="MCP Client CLI - Call MCP server tools")
console = Console()


def get_client() -> MCPClient:
    """Get configured MCP client."""
    url = os.getenv("MCP_SERVER_URL", "http://localhost:3000/mcp")
    return MCPClient(url)


def print_json(data: dict, title: str = "Result"):
    """Pretty print JSON result."""
    rprint(Panel(json.dumps(data, indent=2), title=title, border_style="green"))


def print_error(message: str):
    """Print error message."""
    rprint(Panel(message, title="Error", border_style="red"))


@app.command()
def init():
    """Initialize MCP session and list available tools."""
    with get_client() as client:
        try:
            info = client.initialize()
            rprint(Panel("MCP Session Initialized", title="Status", border_style="green"))

            tools = client.list_tools()
            table = Table(title="Available Tools")
            table.add_column("Tool", style="cyan")
            table.add_column("Description", style="white")

            for tool in tools:
                table.add_row(tool["name"], tool.get("description", "")[:60])

            console.print(table)
        except MCPError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Connection error: {e}")


@app.command()
def search_patients(
    name: str = typer.Argument(..., help="Patient name"),
    birth_date: str = typer.Argument(..., help="Birth date (YYYY-MM-DD)"),
):
    """Search for a patient by name and birth date."""
    with get_client() as client:
        try:
            client.initialize()
            result = client.search_patients(name, birth_date)
            print_json(result, "Patient Search Result")
        except MCPError as e:
            print_error(str(e))


@app.command()
def create_patient(
    name: str = typer.Argument(..., help="Patient full name"),
    birth_date: str = typer.Argument(..., help="Birth date (YYYY-MM-DD)"),
    phone: str = typer.Argument(..., help="Phone with country code"),
):
    """Create a new patient record."""
    with get_client() as client:
        try:
            client.initialize()
            result = client.create_patient(name, birth_date, phone)
            print_json(result, "Patient Created")
        except MCPError as e:
            print_error(str(e))


@app.command()
def list_practitioners(
    specialty: str = typer.Argument(
        ..., help="Specialty code: general-medicine, cardiology, dermatology, obgyn, orthopedics"
    ),
):
    """List practitioners by specialty."""
    with get_client() as client:
        try:
            client.initialize()
            result = client.list_practitioners(specialty)
            print_json(result, f"Practitioners - {specialty}")
        except MCPError as e:
            print_error(str(e))


@app.command()
def get_slots(
    practitioner_id: str = typer.Argument(..., help="Practitioner ID"),
    date: str = typer.Argument(
        ..., help="Date (YYYY-MM-DD) or Unix timestamp"
    ),
):
    """Get available appointment slots for a practitioner on a date."""
    with get_client() as client:
        try:
            client.initialize()
            # Convert date string to timestamp if needed
            if "-" in date:
                dt = datetime.strptime(date, "%Y-%m-%d")
                timestamp = int(dt.timestamp())
            else:
                timestamp = int(date)

            result = client.get_slots(practitioner_id, timestamp)
            print_json(result, f"Available Slots - {date}")
        except MCPError as e:
            print_error(str(e))


@app.command()
def book(
    patient_id: str = typer.Argument(..., help="Patient ID"),
    slot_id: str = typer.Argument(..., help="Slot ID"),
    reason: str = typer.Option("", help="Reason for visit"),
):
    """Book an appointment."""
    with get_client() as client:
        try:
            client.initialize()
            result = client.create_appointment(patient_id, slot_id, reason)
            print_json(result, "Appointment Booked")
        except MCPError as e:
            print_error(str(e))


@app.command()
def reschedule(
    appointment_id: str = typer.Argument(..., help="Existing appointment ID"),
    new_slot_id: str = typer.Argument(..., help="New slot ID"),
):
    """Reschedule an existing appointment."""
    with get_client() as client:
        try:
            client.initialize()
            result = client.update_appointment(appointment_id, new_slot_id)
            print_json(result, "Appointment Rescheduled")
        except MCPError as e:
            print_error(str(e))


@app.command()
def demo():
    """Run a complete demo workflow."""
    with get_client() as client:
        try:
            rprint("\n[bold cyan]═══ MCP Client Demo ═══[/bold cyan]\n")

            # 1. Initialize
            rprint("[yellow]1. Initializing MCP session...[/yellow]")
            client.initialize()
            rprint("[green]   ✓ Session initialized[/green]\n")

            # 2. List tools
            rprint("[yellow]2. Listing available tools...[/yellow]")
            tools = client.list_tools()
            for t in tools:
                rprint(f"   • {t['name']}")
            rprint()

            # 3. Search patient
            rprint("[yellow]3. Searching for patient 'John Smith'...[/yellow]")
            result = client.search_patients("John Smith", "1985-03-15")
            if result.get("found"):
                patient_id = result["patient_id"]
                rprint(f"[green]   ✓ Found: {patient_id}[/green]\n")
            else:
                rprint("[red]   ✗ Patient not found[/red]\n")
                return

            # 4. Find cardiologist
            rprint("[yellow]4. Finding cardiologists...[/yellow]")
            result = client.list_practitioners("cardiology")
            if result.get("practitioners"):
                practitioner = result["practitioners"][0]
                practitioner_id = practitioner["practitioner_id"]
                rprint(f"[green]   ✓ Found: {practitioner['name']}[/green]\n")
            else:
                rprint("[red]   ✗ No cardiologists found[/red]\n")
                return

            # 5. Get slots
            rprint("[yellow]5. Checking available slots...[/yellow]")
            # Use tomorrow
            tomorrow = int(datetime.now().timestamp()) + 86400
            result = client.get_slots(practitioner_id, tomorrow)
            if result.get("slots"):
                slot = result["slots"][0]
                rprint(f"[green]   ✓ Found {len(result['slots'])} slots[/green]")
                rprint(f"   First slot: {slot['start_time']}\n")
            else:
                rprint("[yellow]   No slots available for tomorrow[/yellow]\n")

            rprint("[bold green]Demo complete![/bold green]")

        except MCPError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
