import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")

from server.database import Base, get_db
from server.main import app
from server.services.blockchain_service import BlockchainService
from server.services.loyalty_service import LoyaltyService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    class DummyBlockchainService(BlockchainService):
        def __init__(self):
            super().__init__(rpc_url="http://127.0.0.1:8545", contract_address="0x123")

        def get_balance(self, wallet_address: str) -> int:
            return 500 if wallet_address == "0xabc" else 0

        def mint(self, to_address: str, amount: int, reference: str, private_key: str) -> dict:
            return {"tx_hash": "0xabc123", "status": "success"}

        def burn(self, from_address: str, amount: int, reference: str, private_key: str) -> dict:
            return {"tx_hash": "0xdef456", "status": "success"}

        def transfer(self, from_address: str, to_address: str, amount: int, private_key: str) -> dict:
            return {"tx_hash": "0x789", "status": "success"}

        def wait_for_transaction(self, tx_hash: str) -> dict:
            return {"status": 1}

        def get_transaction(self, tx_hash: str) -> dict:
            return {"hash": tx_hash, "status": "success"}

    monkeypatch.setattr("server.main.get_blockchain_service", lambda: DummyBlockchainService())
    monkeypatch.setattr("server.api.loyalty.get_blockchain_service", lambda: DummyBlockchainService())
    monkeypatch.setattr("server.services.loyalty_service.get_blockchain_service", lambda: DummyBlockchainService())

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def loyalty_service(db_session):
    blockchain_service = BlockchainService(rpc_url="http://127.0.0.1:8545", contract_address="0x123")
    return LoyaltyService(db=db_session, blockchain_service=blockchain_service)
