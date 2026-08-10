def test_earn_point(client):
    response = client.post(
        "/loyalty/earn",
        json={"user_wallet": "0xabc", "partner": "coffee", "amount": 500, "reference": "ORDER-001"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_redeem_point(client):
    client.post(
        "/loyalty/earn",
        json={"user_wallet": "0xabc", "partner": "coffee", "amount": 500, "reference": "ORDER-001"},
    )
    response = client.post(
        "/loyalty/redeem",
        json={"user_wallet": "0xabc", "partner": "cinema", "amount": 100, "reference": "TICKET-001"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
