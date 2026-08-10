from __future__ import annotations

import typer

app = typer.Typer()


@app.command()
def create(name: str, wallet: str):
    print(f"create user {name} {wallet}")
