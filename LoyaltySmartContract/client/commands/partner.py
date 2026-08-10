from __future__ import annotations

import typer

app = typer.Typer()


@app.command()
def list():
    print("list partners")
