def test_partner(client):
    response = client.get("/partners")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == "coffee" for item in payload)
    assert any(item["id"] == "cinema" for item in payload)
