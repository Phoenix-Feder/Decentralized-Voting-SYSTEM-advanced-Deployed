import json
from pathlib import Path
from web3 import Web3
import time

# 1. Connection Setup
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# 2. Permanent Admin Credentials (from your Voting Workspace)
ADMIN_ADDRESS = Web3.to_checksum_address("0x861Cf83aDb7bceCfE5497A78c8C2237b752d1669")
PRIVATE_KEY = "0x564408156ea9178e21d087189cbe2c2d3c077d00141ed4e0ae65c89b34971a3b"

# 3. Path Setup
BLOCKCHAIN_DIR = Path(__file__).resolve().parent
with open(BLOCKCHAIN_DIR / "contract_config.json") as f:
    config = json.load(f)

CONTRACT_ADDRESS = Web3.to_checksum_address(config["contract_address"])
with open(BLOCKCHAIN_DIR / "abi" / "AdvancedVotingSystem.json") as f:
    ABI = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# 4. Write Function
def add_candidate(candidate_name: str) -> str:
    """Sends a signed transaction to add a candidate to the blockchain"""
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)
    
    tx = contract.functions.addCandidate(candidate_name).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })

    # Sign the transaction
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    
    # Send the raw transaction (Note the underscore!)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for the blockchain to confirm the transaction
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()

def register_voter(voter_address: str) -> str:
    """
    Admin-only: Registers a voter wallet address for the current electionId.
    """
    voter_address = Web3.to_checksum_address(voter_address)
    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)

    # Calling 'registerVoter' exactly as named in your Solidity contract
    tx = contract.functions.registerVoter(voter_address).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()

def cast_vote(voter_private_key: str, candidate_id: int) -> str:
    """
    Casts a vote for a candidate. 
    Signed by the voter's private key.
    """
    # Get the address from the private key
    account = w3.eth.account.from_key(voter_private_key)
    voter_address = account.address
    
    nonce = w3.eth.get_transaction_count(voter_address)

    # Calling the 'vote' function from your Solidity contract
    tx = contract.functions.vote(candidate_id).build_transaction({
        "from": voter_address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })

    # Sign with the VOTER'S private key, not the admin's
    signed_tx = w3.eth.account.sign_transaction(tx, voter_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()

def reset_blockchain_election(duration_days=7):
    """
    Resets the election on-chain. 
    Sets startTime to 'now' and endTime to 'now + duration_days'.
    """
    # Get current time and set end time far into the future
    start_time = int(time.time()) - 300  # 5 minutes ago to be safe
    end_time = start_time + (duration_days * 24 * 60 * 60)

    nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)

    # Calling 'resetElection' from your Solidity contract
    tx = contract.functions.resetElection(start_time, end_time).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": w3.eth.chain_id,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex(), start_time, end_time