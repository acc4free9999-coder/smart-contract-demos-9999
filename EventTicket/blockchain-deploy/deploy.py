
import json
import os
import subprocess
import time
from pathlib import Path

from web3 import Web3


# ============================================================
# Configuration
# ============================================================

SOLC_VERSION = "0.8.19"

GANACHE_URL = os.environ.get(
    "GANACHE_URL",
    "http://ganache:8545",
)

EVENT_NAME = os.environ.get(
    "EVENT_NAME",
    "Demo Concert 2026",
)

OUTPUT_DIR = Path(
    os.environ.get(
        "OUTPUT_DIR",
        "/shared",
    )
)

CONTRACT_PATH = Path(
    "/app/contracts/EventTicket.sol"
)


# ============================================================
# Ganache
# ============================================================

def wait_for_ganache(
    w3: Web3,
    retries: int = 30,
    delay: int = 2,
):
    """
    Wait until Ganache is ready.
    """

    for i in range(retries):
        try:
            if w3.is_connected():
                print(
                    "Da ket noi Ganache thanh cong."
                )
                return

        except Exception:
            pass

        print(
            f"Dang cho Ganache khoi dong... "
            f"({i + 1}/{retries})"
        )

        time.sleep(delay)

    raise RuntimeError(
        "Khong the ket noi den Ganache "
        "sau nhieu lan thu."
    )


# ============================================================
# Solidity Compiler
# ============================================================

def check_solc():
    """
    Check that solc-js is installed.

    We use solc-js instead of the native solc binary
    because this Docker image may run on ARM64.
    """

    try:
        result = subprocess.run(
            [
                "solcjs",
                "--version",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    except FileNotFoundError as exc:
        raise RuntimeError(
            "Khong tim thay 'solcjs' trong Docker image.\n"
            f"Hay cai solc-js version {SOLC_VERSION}."
        ) from exc

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Khong the chay solcjs."
        ) from exc

    version_output = result.stdout.strip()

    print("Solidity compiler:")
    print(version_output)

    if SOLC_VERSION not in version_output:
        raise RuntimeError(
            "Khong dung Solidity compiler version.\n"
            f"Expected: {SOLC_VERSION}\n"
            f"Actual: {version_output}"
        )


# ============================================================
# Compile Smart Contract
# ============================================================

def compile_contract():
    """
    Compile EventTicket.sol using solc-js.

    No Internet connection is required at runtime.
    """

    if not CONTRACT_PATH.exists():
        raise FileNotFoundError(
            "Khong tim thay smart contract:\n"
            f"{CONTRACT_PATH}"
        )

    check_solc()

    source = CONTRACT_PATH.read_text(
        encoding="utf-8",
    )

    compiler_input = {
        "language": "Solidity",
        "sources": {
            "EventTicket.sol": {
                "content": source,
            },
        },
        "settings": {
            "optimizer": {
                "enabled": False,
                "runs": 200,
            },
            "outputSelection": {
                "*": {
                    "*": [
                        "abi",
                        "evm.bytecode.object",
                    ],
                },
            },
        },
    }

    print(
        f"Dang compile smart contract "
        f"bang solc-js {SOLC_VERSION}..."
    )

    try:
        result = subprocess.run(
            [
                "solcjs",
                "--standard-json",
            ],
            input=json.dumps(
                compiler_input
            ),
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError as exc:
        raise RuntimeError(
            "Khong tim thay solcjs."
        ) from exc

    if result.returncode != 0:

        print(
            "Solidity compiler stderr:"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "Compile smart contract that bai."
        )

    stdout = result.stdout.strip()

    if not stdout:

        print(
            "Solidity compiler stderr:"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "solcjs khong tra ve output."
        )

    # --------------------------------------------------------
    # solc-js may output warnings/messages before JSON.
    # Find the first JSON object.
    # --------------------------------------------------------

    json_start = stdout.find("{")

    if json_start == -1:

        print(
            "solcjs output:"
        )

        print(
            stdout
        )

        raise RuntimeError(
            "Khong tim thay JSON output "
            "tu solcjs."
        )

    stdout = stdout[json_start:]

    try:

        compiled = json.loads(
            stdout
        )

    except json.JSONDecodeError as exc:

        print(
            "Invalid solcjs JSON output:"
        )

        print(
            stdout
        )

        raise RuntimeError(
            "Khong parse duoc output "
            "cua solcjs."
        ) from exc

    # --------------------------------------------------------
    # Check Solidity compiler errors
    # --------------------------------------------------------

    errors = compiled.get(
        "errors",
        [],
    )

    fatal_errors = [
        error
        for error in errors
        if error.get("severity") == "error"
    ]

    # Print warnings
    warnings = [
        error
        for error in errors
        if error.get("severity") == "warning"
    ]

    for warning in warnings:

        print(
            "Solidity warning:"
        )

        print(
            warning.get(
                "formattedMessage",
                warning,
            )
        )

    # Print fatal errors
    if fatal_errors:

        print(
            "Solidity compile errors:"
        )

        for error in fatal_errors:

            print(
                error.get(
                    "formattedMessage",
                    error,
                )
            )

        raise RuntimeError(
            "Compile smart contract that bai."
        )

    # --------------------------------------------------------
    # Find EventTicket contract
    # --------------------------------------------------------

    contracts = compiled.get(
        "contracts",
        {},
    )

    event_ticket_file = contracts.get(
        "EventTicket.sol",
        {},
    )

    contract_data = event_ticket_file.get(
        "EventTicket",
    )

    if contract_data is None:

        available_contracts = list(
            event_ticket_file.keys()
        )

        raise RuntimeError(
            "Khong tim thay contract "
            "'EventTicket'.\n"
            f"Available contracts: "
            f"{available_contracts}"
        )

    # --------------------------------------------------------
    # ABI
    # --------------------------------------------------------

    abi = contract_data.get(
        "abi",
    )

    if abi is None:

        raise RuntimeError(
            "Khong tim thay ABI cua EventTicket."
        )

    # --------------------------------------------------------
    # Bytecode
    # --------------------------------------------------------

    bytecode = (
        contract_data
        .get("evm", {})
        .get("bytecode", {})
        .get("object", "")
    )

    if not bytecode:

        raise RuntimeError(
            "Bytecode cua EventTicket dang rong."
        )

    print(
        "Compile smart contract thanh cong."
    )

    return abi, bytecode


# ============================================================
# Save Deployment Information
# ============================================================

def save_deployment_info(
    abi,
    contract_address,
    deployer,
    accounts,
    chain_id,
    transaction_hash,
):
    """
    Save ABI, contract address and deployment
    information into /shared.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # ABI
    # --------------------------------------------------------

    abi_path = (
        OUTPUT_DIR / "abi.json"
    )

    abi_path.write_text(
        json.dumps(
            abi,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Contract address
    # --------------------------------------------------------

    address_path = (
        OUTPUT_DIR / "address.txt"
    )

    address_path.write_text(
        contract_address,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Organizer / deployer
    # --------------------------------------------------------

    organizer_path = (
        OUTPUT_DIR / "organizer.txt"
    )

    organizer_path.write_text(
        deployer,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Ganache accounts
    # --------------------------------------------------------

    accounts_path = (
        OUTPUT_DIR / "accounts.json"
    )

    accounts_path.write_text(
        json.dumps(
            accounts,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Deployment metadata
    # --------------------------------------------------------

    deployment = {
        "eventName": EVENT_NAME,
        "contractAddress": contract_address,
        "organizer": deployer,
        "chainId": chain_id,
        "ganacheUrl": GANACHE_URL,
        "solidityVersion": SOLC_VERSION,
        "transactionHash": transaction_hash,
    }

    deployment_path = (
        OUTPUT_DIR / "deployment.json"
    )

    deployment_path.write_text(
        json.dumps(
            deployment,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Da ghi ABI + dia chi contract "
        f"vao volume dung chung "
        f"({OUTPUT_DIR})."
    )

    print(
        "Files:"
    )

    print(
        f"  - {abi_path}"
    )

    print(
        f"  - {address_path}"
    )

    print(
        f"  - {organizer_path}"
    )

    print(
        f"  - {accounts_path}"
    )

    print(
        f"  - {deployment_path}"
    )


# ============================================================
# Deploy Contract
# ============================================================

def deploy():
    """
    Main deployment flow:

    1. Connect to Ganache
    2. Wait for Ganache
    3. Compile EventTicket.sol
    4. Get deployer account
    5. Deploy contract
    6. Wait for transaction
    7. Save deployment information
    """

    print(
        "========================================"
    )

    print(
        "Event Ticket Deployment"
    )

    print(
        "========================================"
    )

    print(
        f"Ganache URL : {GANACHE_URL}"
    )

    print(
        f"Event name  : {EVENT_NAME}"
    )

    print(
        f"Contract    : {CONTRACT_PATH}"
    )

    print(
        f"Output dir  : {OUTPUT_DIR}"
    )

    print(
        f"Solidity    : {SOLC_VERSION}"
    )

    # --------------------------------------------------------
    # Connect to Ganache
    # --------------------------------------------------------

    w3 = Web3(
        Web3.HTTPProvider(
            GANACHE_URL
        )
    )

    wait_for_ganache(
        w3
    )

    # --------------------------------------------------------
    # Chain ID
    # --------------------------------------------------------

    chain_id = w3.eth.chain_id

    print(
        f"Ganache chain ID: {chain_id}"
    )

    # --------------------------------------------------------
    # Get accounts
    # --------------------------------------------------------

    accounts = w3.eth.accounts

    if not accounts:

        raise RuntimeError(
            "Ganache khong co account nao."
        )

    deployer = accounts[0]

    print(
        f"Deployer account: {deployer}"
    )

    # --------------------------------------------------------
    # Check deployer balance
    # --------------------------------------------------------

    balance = w3.eth.get_balance(
        deployer
    )

    balance_eth = w3.from_wei(
        balance,
        "ether",
    )

    print(
        f"Deployer balance: "
        f"{balance_eth} ETH"
    )

    # --------------------------------------------------------
    # Compile
    # --------------------------------------------------------

    print(
        "Dang bien dich smart contract..."
    )

    abi, bytecode = (
        compile_contract()
    )

    # --------------------------------------------------------
    # Create contract
    # --------------------------------------------------------

    Contract = w3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )

    # --------------------------------------------------------
    # Deploy contract
    # --------------------------------------------------------

    print(
        f"Dang deploy EventTicket "
        f"voi event: {EVENT_NAME}"
    )

    try:

        transaction = (
            Contract.constructor(
                EVENT_NAME
            ).build_transaction(
                {
                    "from": deployer,
                    "nonce": w3.eth.get_transaction_count(
                        deployer
                    ),
                    "chainId": chain_id,
                    "gas": 3_000_000,
                    "gasPrice": w3.eth.gas_price,
                }
            )
        )

        tx_hash = w3.eth.send_transaction(
            transaction
        )

    except Exception as exc:

        raise RuntimeError(
            "Khong the gui transaction deploy "
            f"contract: {exc}"
        ) from exc

    print(
        f"Transaction hash: "
        f"{tx_hash.hex()}"
    )

    # --------------------------------------------------------
    # Wait for receipt
    # --------------------------------------------------------

    print(
        "Dang cho transaction duoc confirm..."
    )

    receipt = (
        w3.eth.wait_for_transaction_receipt(
            tx_hash
        )
    )

    # --------------------------------------------------------
    # Check transaction status
    # --------------------------------------------------------

    if receipt.status != 1:

        raise RuntimeError(
            "Transaction deploy contract "
            "that bai."
        )

    contract_address = (
        receipt.contractAddress
    )

    if not contract_address:

        raise RuntimeError(
            "Ganache khong tra ve "
            "contract address."
        )

    print(
        "Contract da duoc deploy "
        f"tai dia chi: {contract_address}"
    )

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    save_deployment_info(
        abi=abi,
        contract_address=contract_address,
        deployer=deployer,
        accounts=accounts,
        chain_id=chain_id,
        transaction_hash=tx_hash.hex(),
    )

    print(
        "Deploy hoan tat."
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    deploy()

