from server.services.loyalty_service import LoyaltyService


def test_token_mint(loyalty_service: LoyaltyService):
    result = loyalty_service.earn_points(
        user_wallet="0xabc",
        partner_id="coffee",
        amount=500,
        reference="ORDER-001",
    )
    assert result["success"] is True
    assert result["amount"] == 500


def test_token_burn(loyalty_service: LoyaltyService):
    loyalty_service.earn_points(user_wallet="0xabc", partner_id="coffee", amount=500, reference="ORDER-001")
    result = loyalty_service.redeem_points(
        user_wallet="0xabc",
        partner_id="cinema",
        amount=100,
        reference="TICKET-001",
    )
    assert result["success"] is True
    assert result["amount"] == 100
