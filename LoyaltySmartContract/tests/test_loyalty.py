def test_balance(client):
    response = client.get("/loyalty/balance/0xabc")
    assert response.status_code == 200
    assert response.json()["balance"] == "500"


def test_transaction_history(client):
    client.post(
        "/loyalty/earn",
        json={"user_wallet": "0xabc", "partner": "coffee", "amount": 500, "reference": "ORDER-001"},
    )
    response = client.get("/loyalty/transactions/0xabc")
    assert response.status_code == 200
    assert len(response.json()) == 1
