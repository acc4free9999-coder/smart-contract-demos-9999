import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

app = typer.Typer(add_completion=False, help="CLI client for the loyalty demo")
console = Console()
BASE_URL = "http://127.0.0.1:8000"


@app.command()
def balance(wallet: str = typer.Option("0xabc", "--wallet")):
    response = httpx.get(f"{BASE_URL}/loyalty/balance/{wallet}", timeout=10.0)
    response.raise_for_status()
    payload = response.json()
    console.print(f"[bold green]{payload['wallet']}[/bold green]: {payload['balance']} {payload['token']}")


@app.command()
def earn(partner: str, amount: int, wallet: str = typer.Option("0xabc", "--wallet"), reference: str = typer.Option("ORDER-001", "--reference")):
    response = httpx.post(
        f"{BASE_URL}/loyalty/earn",
        json={"user_wallet": wallet, "partner": partner, "amount": amount, "reference": reference},
        timeout=10.0,
    )
    response.raise_for_status()
    payload = response.json()
    console.print(f"Awarded {payload['amount']} {payload['token']} via tx {payload['tx_hash']}")


@app.command()
def redeem(partner: str, amount: int, wallet: str = typer.Option("0xabc", "--wallet"), reference: str = typer.Option("TICKET-001", "--reference")):
    response = httpx.post(
        f"{BASE_URL}/loyalty/redeem",
        json={"user_wallet": wallet, "partner": partner, "amount": amount, "reference": reference},
        timeout=10.0,
    )
    response.raise_for_status()
    payload = response.json()
    console.print(f"Redeemed {payload['amount']} {payload['token']} via tx {payload['tx_hash']}")


@app.command()
def history(wallet: str = typer.Option("0xabc", "--wallet")):
    response = httpx.get(f"{BASE_URL}/loyalty/transactions/{wallet}", timeout=10.0)
    response.raise_for_status()
    rows = response.json()
    table = Table(title="Transaction History")
    table.add_column("Type")
    table.add_column("Partner")
    table.add_column("Amount")
    table.add_column("Reference")
    table.add_column("Tx Hash")
    for row in rows:
        table.add_row(row["type"], row["partner"], str(row["amount"]), row["reference"], row["tx_hash"])
    console.print(table)


@app.command()
def partners():
    response = httpx.get(f"{BASE_URL}/partners", timeout=10.0)
    response.raise_for_status()
    rows = response.json()
    table = Table(title="Partners")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Earn Rate")
    table.add_column("Redeem Rate")
    for row in rows:
        table.add_row(row["id"], row["name"], str(row.get("earn_rate", "")), str(row.get("redeem_rate", "")))
    console.print(table)


if __name__ == "__main__":
    app()
