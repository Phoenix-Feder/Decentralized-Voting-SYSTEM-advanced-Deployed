import json
from pathlib import Path
from web3 import Web3

# ---------- GANACHE CONFIG ----------
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    print(f"❌ Critical Error: Ganache is not running at {GANACHE_URL}")
    exit()

# ---------- ADMIN WALLET ----------
# Permanent address and key for your local Ganache environment
ADMIN_ADDRESS = Web3.to_checksum_address("0x861Cf83aDb7bceCfE5497A78c8C2237b752d1669")
PRIVATE_KEY = "0x564408156ea9178e21d087189cbe2c2d3c077d00141ed4e0ae65c89b34971a3b"
CHAIN_ID = w3.eth.chain_id 

# ---------- LOAD ABI & BYTECODE ----------
BASE_DIR = Path(__file__).resolve().parent
ABI_PATH = BASE_DIR / "abi" / "AdvancedVotingSystem.json"
BYTECODE_PATH = BASE_DIR / "bytecode.txt"

try:
    with open(ABI_PATH) as f:
        ABI = json.load(f)

    with open(BYTECODE_PATH) as f:
        BYTECODE = f.read().strip()
except FileNotFoundError as e:
    print(f"❌ File not found: {e.filename}. Please check the 'abi' folder.")
    exit()

# ---------- DEPLOY FUNCTION ----------
def deploy_election() -> str:
    """ 
    Deploys the AdvancedVotingSystem contract. 
    Returns the newly deployed contract address.
    """
    contract = w3.eth.contract(abi=ABI, bytecode=BYTECODE)
    
    # Nonce management is automatic here, but we fetch it for the manual sign
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)

    # Build transaction for the constructor (takes no arguments)
    tx_params = {
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 6000000,
        "gasPrice": w3.to_wei('2', 'gwei'),
        "chainId": CHAIN_ID,
    }

    print("🚀 Deploying contract to the blockchain...")
    transaction = contract.constructor().build_transaction(tx_params)

    # Sign the transaction
    signed_tx = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    
    # web3.py v6+ uses .raw_transaction (snake_case)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"⏳ Transaction sent! Hash: {tx_hash.hex()}")
    
    # Wait for the block to be mined
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Check for contractAddress in the receipt
    if receipt.contractAddress:
        return receipt.contractAddress
    else:
        raise Exception("Deployment failed: No contract address found in receipt.")

# ---------- HELPER FOR CONTRACT INTERACTION ----------
def get_voting_contract():
    """ 
    Utility to get the contract instance using the address saved in config.
    Used by other scripts to interact with the deployed contract.
    """
    config_path = BASE_DIR.parent / "contract_config.json"
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        address = Web3.to_checksum_address(config["contract_address"])
        return w3.eth.contract(address=address, abi=ABI)
    except (FileNotFoundError, KeyError) as e:
        print(f"❌ Configuration error: {e}. Ensure 'test_deploy.py' has run successfully.")
        return None