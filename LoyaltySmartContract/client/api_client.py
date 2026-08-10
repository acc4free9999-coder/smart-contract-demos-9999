from __future__ import annotations

import httpx


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    def get_balance(self, wallet: str) -> dict:
        response = httpx.get(f"{self.base_url}/loyalty/balance/{wallet}", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def earn_points(self, wallet: str, partner: str, amount: int, reference: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/loyalty/earn",
            json={"user_wallet": wallet, "partner": partner, "amount": amount, "reference": reference},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    def redeem_points(self, wallet: str, partner: str, amount: int, reference: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/loyalty/redeem",
            json={"user_wallet": wallet, "partner": partner, "amount": amount, "reference": reference},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
