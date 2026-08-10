import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env", override=False)


def deploy_contract():
    rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("ADMIN_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("ADMIN_PRIVATE_KEY is required")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Unable to connect to {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)

    contract_path = ROOT / "contracts" / "LoyaltyToken.sol"
    if not contract_path.exists():
        raise FileNotFoundError(contract_path)

    print("Deployment script is ready; install solc and compile the contract to deploy it in a real environment.")
    return {"status": "script_ready", "rpc_url": rpc_url, "deployer": account.address}


if __name__ == "__main__":
    print(deploy_contract())
