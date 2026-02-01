import json
import os
from pathlib import Path
from web3 import Web3

# 1. Configuration & Connection
# Ensure this matches your Ganache settings (7545 for UI, 8545 for CLI)
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Get the directory where this file (contract_reader.py) is located
BASE_DIR = Path(__file__).resolve().parent

def load_contract():
    try:
        # Load contract address from config
        config_path = BASE_DIR / "contract_config.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        
        contract_address = Web3.to_checksum_address(config["contract_address"])

        # Load ABI from the 'abi' sub-folder
        abi_path = BASE_DIR / "abi" / "AdvancedVotingSystem.json"
        
        if not abi_path.exists():
            raise FileNotFoundError(f"ABI file not found at: {abi_path}")

        with open(abi_path, "r") as f:
            contract_json = json.load(f)
            # Handle Truffle vs. Raw ABI formats
            abi = contract_json["abi"] if isinstance(contract_json, dict) and "abi" in contract_json else contract_json

        return w3.eth.contract(address=contract_address, abi=abi)
    
    except Exception as e:
        print(f"❌ Error initializing contract: {e}")
        return None

# Initialize the contract instance safely
contract = load_contract()

def get_election_info():
    """Retrieves general election state data."""
    if not contract: return {"error": "Contract not loaded"}
    
    return {
        "electionId": contract.functions.electionId().call(),
        "startTime": contract.functions.startTime().call(),
        "endTime": contract.functions.endTime().call(),
        "candidatesCount": contract.functions.candidatesCount().call(),
        "contractAddress": contract.address,
    }

def get_candidates():
    """Returns a list of all candidates and their current tallies."""
    if not contract: return []
    
    count = contract.functions.candidatesCount().call()
    result = []
    for i in range(1, count + 1):
        # Matches the [id, name, voteCount] structure in your Solidity mapping
        cand = contract.functions.candidates(i).call()
        result.append({
            "id": cand[0], 
            "name": cand[1], 
            "votes": cand[2]
        })
    return result

def get_winner():
    """Determines the candidate with the highest votes."""
    if not contract: return "No Contract", 0, 0
    
    total_candidates = contract.functions.candidatesCount().call()
    winner_name = "No Winner"
    max_votes = -1
    winner_id = 0

    for i in range(1, total_candidates + 1):
        candidate = contract.functions.candidates(i).call()
        if candidate[2] > max_votes:
            max_votes = candidate[2]
            winner_name = candidate[1]
            winner_id = candidate[0]
            
    return winner_name, max_votes, winner_id

def get_vote_history():
    """Retrieves 'VoteCast' events for the audit trail."""
    if not contract: return []
    
    try:
        # Fetching events from genesis to latest block
        events = contract.events.VoteCast.get_logs(from_block=0)

        audit_trail = []
        for event in events:
            audit_trail.append({
                "voter": event.args.voter,
                "candidate_id": event.args.candidateId,
                "election_id": event.args.electionId,
                "transaction_hash": event.transactionHash.hex(),
                "block_number": event.blockNumber
            })
        
        return audit_trail[::-1] # Return newest votes first
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []