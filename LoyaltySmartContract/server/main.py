from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from server.api import loyalty, partners, transactions, users
from server.database import Base, engine
from server.models import partner, transaction, user
from server.services.loyalty_service import get_blockchain_service

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Partner Loyalty Blockchain Demo",
    description="Educational demo of a shared loyalty token between coffee, cinema, and bank partners.",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(partners.router)
app.include_router(loyalty.router)
app.include_router(transactions.router)


@app.get("/", response_class=HTMLResponse, summary="Project landing page")
def root() -> str:
    return "<h1>Multi-Partner Loyalty Blockchain Demo</h1><p>Use /docs for API documentation.</p>"


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/blockchain", summary="Blockchain connectivity")
def blockchain_status() -> dict[str, object]:
    try:
        service = get_blockchain_service()
        service._ensure_connected()
        return {"status": "connected", "rpc": service.rpc_url}
    except Exception as exc:  # pragma: no cover - informational endpoint
        return {"status": "error", "error": str(exc)}
