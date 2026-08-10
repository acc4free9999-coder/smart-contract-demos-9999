import os
from typing import Any

from web3 import Web3
from web3.exceptions import ContractLogicError

from server.config import BLOCKCHAIN_RPC_URL, LOYALTY_CONTRACT_ADDRESS, MINTER_PRIVATE_KEY, BURNER_PRIVATE_KEY


class BlockchainService:
    def __init__(self, rpc_url: str | None = None, contract_address: str | None = None):
        self.rpc_url = rpc_url or BLOCKCHAIN_RPC_URL
        self.contract_address = contract_address or LOYALTY_CONTRACT_ADDRESS
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self._contract = None

    def _ensure_connected(self) -> None:
        if not self.w3.is_connected():
            raise RuntimeError(f"Unable to connect to blockchain RPC: {self.rpc_url}")

    def _load_contract(self) -> Any:
        if self._contract is None:
            self._ensure_connected()
            abi = [
                {"inputs": [{"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}, {"internalType": "string", "name": "reference", "type": "string"}], "name": "mint", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                {"inputs": [{"internalType": "address", "name": "from", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}, {"internalType": "string", "name": "reference", "type": "string"}], "name": "burn", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
                {"inputs": [{"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
                {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "partner", "type": "address"}, {"indexed": True, "internalType": "address", "name": "customer", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}, {"indexed": False, "internalType": "string", "name": "reference", "type": "string"}], "name": "LoyaltyMinted", "type": "event"},
                {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "partner", "type": "address"}, {"indexed": True, "internalType": "address", "name": "customer", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}, {"indexed": False, "internalType": "string", "name": "reference", "type": "string"}], "name": "LoyaltyRedeemed", "type": "event"},
            ]
            self._contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
        return self._contract

    def get_balance(self, wallet_address: str) -> int:
        contract = self._load_contract()
        return int(contract.functions.balanceOf(wallet_address).call())

    def mint(self, to_address: str, amount: int, reference: str, private_key: str) -> dict[str, Any]:
        contract = self._load_contract()
        account = self.w3.eth.account.from_key(private_key)
        tx = contract.functions.mint(to_address, amount, reference).build_transaction(
            {
                "from": account.address,
                "nonce": self.w3.eth.get_transaction_count(account.address),
                "gas": 300000,
                "gasPrice": self.w3.to_wei("20", "gwei"),
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"tx_hash": self.w3.to_hex(tx_hash), "status": "pending"}

    def burn(self, from_address: str, amount: int, reference: str, private_key: str) -> dict[str, Any]:
        contract = self._load_contract()
        account = self.w3.eth.account.from_key(private_key)
        tx = contract.functions.burn(from_address, amount, reference).build_transaction(
            {
                "from": account.address,
                "nonce": self.w3.eth.get_transaction_count(account.address),
                "gas": 300000,
                "gasPrice": self.w3.to_wei("20", "gwei"),
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"tx_hash": self.w3.to_hex(tx_hash), "status": "pending"}

    def transfer(self, from_address: str, to_address: str, amount: int, private_key: str) -> dict[str, Any]:
        contract = self._load_contract()
        account = self.w3.eth.account.from_key(private_key)
        tx = contract.functions.transfer(to_address, amount).build_transaction(
            {
                "from": from_address,
                "nonce": self.w3.eth.get_transaction_count(from_address),
                "gas": 300000,
                "gasPrice": self.w3.to_wei("20", "gwei"),
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"tx_hash": self.w3.to_hex(tx_hash), "status": "pending"}

    def wait_for_transaction(self, tx_hash: str) -> dict[str, Any]:
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return {"status": receipt.status, "blockNumber": receipt.blockNumber}

    def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        return {"hash": tx_hash, "status": receipt.status if receipt else "pending"}
