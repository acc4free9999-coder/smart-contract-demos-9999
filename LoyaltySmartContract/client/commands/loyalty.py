from __future__ import annotations

import typer

app = typer.Typer()


@app.command()
def balance(wallet: str):
    print(f"balance for {wallet}")
