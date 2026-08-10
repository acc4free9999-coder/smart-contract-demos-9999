import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    response = httpx.post(f"{BASE_URL}/users", json={"name": "Alice", "wallet_address": "0xabc"}, timeout=10.0)
    response.raise_for_status()
    print(f"Seeded Alice: {response.json()}")


if __name__ == "__main__":
    main()
