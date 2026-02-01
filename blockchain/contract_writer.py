import json
import time
from pathlib import Path
from web3 import Web3

# 1. Connection Setup
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# 2. Permanent Admin Credentials
ADMIN_ADDRESS = Web3.to_checksum_address("0x861Cf83aDb7bceCfE5497A78c8C2237b752d1669")
PRIVATE_KEY = "0x564408156ea9178e21d087189cbe2c2d3c077d00141ed4e0ae65c89b34971a3b"

# 3. Path Setup - Adjusted to find config in the parent directory
BLOCKCHAIN_DIR = Path(__file__).resolve().parent
with open(BLOCKCHAIN_DIR.parent / "contract_config.json") as f:
    config = json.load(f)

CONTRACT_ADDRESS = Web3.to_checksum_address(config["contract_address"])
with open(BLOCKCHAIN_DIR / "abi" / "AdvancedVotingSystem.json") as f:
    ABI = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# ---------- HELPER: SIGN & SEND ----------
def _send_admin_tx(transaction):
    signed_tx = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()

# ---------- WRITE FUNCTIONS ----------

def add_candidate(candidate_name: str) -> str:
    """Adds a candidate. Admin only."""
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)
    tx = contract.functions.addCandidate(candidate_name).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    return _send_admin_tx(tx)

def authorize_voter(voter_address: str) -> str:
    """Renamed from registerVoter to match new contract: authorizeVoter"""
    voter_address = Web3.to_checksum_address(voter_address)
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)
    
    tx = contract.functions.authorizeVoter(voter_address).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    return _send_admin_tx(tx)

def revoke_voter(voter_address: str) -> str:
    """NEW FEATURE: Revokes a voter's authorization"""
    voter_address = Web3.to_checksum_address(voter_address)
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)
    
    tx = contract.functions.revokeVoter(voter_address).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    return _send_admin_tx(tx)

def cast_vote(voter_private_key: str, candidate_id: int) -> str:
    """Renamed from vote to match new contract: castVote"""
    account = w3.eth.account.from_key(voter_private_key)
    voter_address = account.address
    nonce = w3.eth.get_transaction_count(voter_address)

    tx = contract.functions.castVote(candidate_id).build_transaction({
        "from": voter_address,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, voter_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()

def setup_blockchain_election(name: str, duration_minutes: int):
    """Replaces reset_blockchain_election to match: setupElection"""
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)

    tx = contract.functions.setupElection(name, duration_minutes).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    tx_hash_hex = _send_admin_tx(tx)
    return tx_hash_hex