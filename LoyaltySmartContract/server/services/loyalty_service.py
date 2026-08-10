from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from server.models.partner import Partner
from server.models.transaction import Transaction
from server.models.user import User
from server.services.blockchain_service import BlockchainService
from server.config import MINTER_PRIVATE_KEY, BURNER_PRIVATE_KEY


def get_blockchain_service() -> BlockchainService:
    return BlockchainService()


class LoyaltyService:
    def __init__(self, db: Session, blockchain_service: BlockchainService | None = None):
        self.db = db
        self.blockchain_service = blockchain_service or get_blockchain_service()

    def create_user(self, name: str, wallet_address: str) -> dict[str, Any]:
        user = User(id=wallet_address, name=name, wallet_address=wallet_address)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return {"id": user.id, "name": user.name, "wallet_address": user.wallet_address}

    def get_partners(self) -> list[dict[str, Any]]:
        partners = self.db.query(Partner).all()
        if not partners:
            self._seed_partners()
            partners = self.db.query(Partner).all()
        return [
            {
                "id": partner.id,
                "name": partner.name,
                "wallet_address": partner.wallet_address,
                "status": partner.status,
                "mint_permission": partner.mint_permission.lower() == "true",
                "burn_permission": partner.burn_permission.lower() == "true",
            }
            for partner in partners
        ]

    def _seed_partners(self) -> None:
        entries = [
            Partner(id="coffee", name="Coffee Shop", wallet_address="0x1111111111111111111111111111111111111111", status="ACTIVE", mint_permission="true", burn_permission="false"),
            Partner(id="cinema", name="Cinema", wallet_address="0x2222222222222222222222222222222222222222", status="ACTIVE", mint_permission="false", burn_permission="true"),
            Partner(id="bank", name="Bank", wallet_address="0x3333333333333333333333333333333333333333", status="ACTIVE", mint_permission="true", burn_permission="true"),
        ]
        self.db.add_all(entries)
        self.db.commit()

    def earn_points(self, user_wallet: str, partner_id: str, amount: int, reference: str) -> dict[str, Any]:
        partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner or partner.status != "ACTIVE":
            raise ValueError("partner inactive")
        if partner.mint_permission.lower() != "true":
            raise PermissionError("partner not authorized")

        tx_result = self.blockchain_service.mint(user_wallet, amount, reference, MINTER_PRIVATE_KEY or "0x")
        self.blockchain_service.wait_for_transaction(tx_result["tx_hash"])
        self.db.add(
            Transaction(
                wallet_address=user_wallet,
                partner=partner_id,
                transaction_type="EARN",
                amount=amount,
                reference=reference,
                tx_hash=tx_result["tx_hash"],
            )
        )
        self.db.commit()
        return {"success": True, "amount": amount, "token": "ULP", "tx_hash": tx_result["tx_hash"]}

    def redeem_points(self, user_wallet: str, partner_id: str, amount: int, reference: str) -> dict[str, Any]:
        partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner or partner.status != "ACTIVE":
            raise ValueError("partner inactive")
        if partner.burn_permission.lower() != "true":
            raise PermissionError("partner not authorized")

        balance = self.blockchain_service.get_balance(user_wallet)
        if balance < amount:
            raise ValueError("insufficient balance")

        tx_result = self.blockchain_service.burn(user_wallet, amount, reference, BURNER_PRIVATE_KEY or "0x")
        self.blockchain_service.wait_for_transaction(tx_result["tx_hash"])
        self.db.add(
            Transaction(
                wallet_address=user_wallet,
                partner=partner_id,
                transaction_type="REDEEM",
                amount=amount,
                reference=reference,
                tx_hash=tx_result["tx_hash"],
            )
        )
        self.db.commit()
        return {"success": True, "amount": amount, "token": "ULP", "tx_hash": tx_result["tx_hash"]}

    def get_balance(self, wallet_address: str) -> str:
        return str(self.blockchain_service.get_balance(wallet_address))

    def get_transactions(self, wallet_address: str) -> list[dict[str, Any]]:
        transactions = self.db.query(Transaction).filter(Transaction.wallet_address == wallet_address).order_by(Transaction.id.desc()).all()
        return [
            {
                "type": tx.transaction_type,
                "partner": tx.partner,
                "amount": tx.amount,
                "tx_hash": tx.tx_hash,
                "reference": tx.reference,
            }
            for tx in transactions
        ]

    def get_settlement(self) -> list[dict[str, Any]]:
        transactions = self.db.query(Transaction).all()
        snapshot: dict[str, dict[str, int]] = {}
        for tx in transactions:
            entry = snapshot.setdefault(tx.partner, {"points_issued": 0, "points_redeemed": 0})
            if tx.transaction_type == "EARN":
                entry["points_issued"] += tx.amount
            else:
                entry["points_redeemed"] += tx.amount
        return [
            {
                "partner": partner_id,
                "points_issued": payload["points_issued"],
                "points_redeemed": payload["points_redeemed"],
                "net_position": payload["points_issued"] - payload["points_redeemed"],
            }
            for partner_id, payload in sorted(snapshot.items())
        ]
