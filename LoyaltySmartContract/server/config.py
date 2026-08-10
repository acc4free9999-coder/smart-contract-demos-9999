import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

BLOCKCHAIN_RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./loyalty.db")
LOYALTY_CONTRACT_ADDRESS = os.getenv("LOYALTY_CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY", "")
MINTER_PRIVATE_KEY = os.getenv("MINTER_PRIVATE_KEY", "")
BURNER_PRIVATE_KEY = os.getenv("BURNER_PRIVATE_KEY", "")
