import json
from pathlib import Path
from web3 import Web3
# Import the established connection and credentials
from web3_config import w3, ADMIN_ADDRESS, PRIVATE_KEY

# 1. Setup Paths
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "contract_config.json"
ABI_PATH = BASE_DIR / "abi" / "AdvancedVotingSystem.json"

# 2. Load Contract Instance
with open(CONFIG_PATH) as f:
    config = json.load(f)

# Use 'contract_address' to match your deployment script standard
CONTRACT_ADDRESS = Web3.to_checksum_address(config["contract_address"])

with open(ABI_PATH) as f:
    ABI = json.load(f)

# Create the contract object here locally
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# 3. Seeding Logic
CANDIDATES = ["Alice Vance", "Bob Smith", "Charlie Brown"]

def seed():
    print(f"🚀 Seeding {len(CANDIDATES)} candidates...")
    for name in CANDIDATES:
        try:
            nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)
            
            # Ensure 'addCandidate' matches your Solidity function name
            tx = contract.functions.addCandidate(name).build_transaction({
                "from": ADMIN_ADDRESS,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": w3.to_wei('2', 'gwei'),
                "chainId": w3.eth.chain_id
            })

            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            # Use raw_transaction (underscore)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction) 
            
            print(f"⏳ Sending {name}... Hash: {tx_hash.hex()}")
            w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Registered {name}")
        except Exception as e:
            print(f"❌ Failed to register {name}: {e}")

if __name__ == "__main__":
    seed()