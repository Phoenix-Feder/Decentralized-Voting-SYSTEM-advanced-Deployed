import json
from pathlib import Path
from web3 import Web3

# ---------- GANACHE CONFIG ----------
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

assert w3.is_connected(), "❌ Ganache not running"

# ---------- ADMIN WALLET ----------
# Using the values from your uploaded screenshot
# blockchain/web3_config.py

# This address now has 100 ETH and will NOT change on restart
ADMIN_ADDRESS = Web3.to_checksum_address("0x861Cf83aDb7bceCfE5497A78c8C2237b752d1669")

# This private key is now permanent for your local project
PRIVATE_KEY = "0x564408156ea9178e21d087189cbe2c2d3c077d00141ed4e0ae65c89b34971a3b"
# DYNAMIC CHAIN ID (Fixes "Invalid signature v value")
CHAIN_ID = w3.eth.chain_id 

# ---------- LOAD ABI & BYTECODE ----------
BASE_DIR = Path(__file__).resolve().parent
ABI_PATH = BASE_DIR / "abi" / "AdvancedVotingSystem.json"
BYTECODE_PATH = BASE_DIR / "bytecode.txt"

with open(ABI_PATH) as f:
    ABI = json.load(f)

with open(BYTECODE_PATH) as f:
    BYTECODE = f.read().strip()

# ---------- DEPLOY FUNCTION ----------
def deploy_election(start_time: int, end_time: int) -> str:
    contract = w3.eth.contract(abi=ABI, bytecode=BYTECODE)
    
    # Nonce management is key for repeated deployments
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)

    tx = contract.constructor(
        start_time,
        end_time
    ).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 6000000,
        "gasPrice": w3.to_wei('2', 'gwei'), # Static price is safer for Ganache
        "chainId": CHAIN_ID,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"⏳ Transaction sent! Hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return receipt.contractAddress