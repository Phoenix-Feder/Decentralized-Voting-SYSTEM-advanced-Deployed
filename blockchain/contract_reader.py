import json
import os
from pathlib import Path
from web3 import Web3

# 1. Configuration & Connection
# Ensure this matches your Ganache settings
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Get the directory where this file (contract_reader.py) is located
BASE_DIR = Path(__file__).resolve().parent

def load_contract():
    try:
        # Load contract address from config
        # Note: Going up one level if config is in the root
        config_path = BASE_DIR.parent / "contract_config.json"
        
        if not config_path.exists():
            print(f"❌ Config file not found at: {config_path}")
            return None

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
    """Retrieves general election state data using updated function names."""
    if not contract: return {"error": "Contract not loaded"}
    
    try:
        return {
            "electionName": contract.functions.electionName().call(),
            "startTime": contract.functions.startTime().call(),
            "endTime": contract.functions.endTime().call(),
            "candidatesCount": contract.functions.candidatesCount().call(),
            "remainingTime": contract.functions.getRemainingTime().call(),
            "contractAddress": contract.address,
        }
    except Exception as e:
        print(f"Error in get_election_info: {e}")
        return {"error": str(e)}

def get_candidates():
    """Returns a list of all candidates and their current tallies."""
    if not contract: return []
    
    try:
        count = contract.functions.candidatesCount().call()
        result = []
        for i in range(1, count + 1):
            # cand returns: [uint256 id, string name, uint256 voteCount, bool exists]
            cand = contract.functions.candidates(i).call()
            
            # Only show candidates that haven't been "removed"
            if cand[3]: 
                result.append({
                    "id": cand[0], 
                    "name": cand[1], 
                    "votes": cand[2]
                })
        return result
    except Exception as e:
        print(f"Error in get_candidates: {e}")
        return []

def get_winner():
    """Determines the candidate with the highest votes."""
    if not contract: return "No Contract", 0, 0
    
    try:
        candidates_list = get_candidates()
        if not candidates_list:
            return "No Candidates", 0, 0
            
        winner = max(candidates_list, key=lambda x: x['votes'])
        return winner['name'], winner['votes'], winner['id']
    except Exception as e:
        print(f"Error in get_winner: {e}")
        return "Error", 0, 0

def get_vote_history():
    """Retrieves 'VoteCast' events for the audit trail."""
    if not contract: return []
    
    try:
        # Fetching events from genesis to latest block
        events = contract.events.VoteCast.get_logs(from_block=0)

        audit_trail = []
        for event in events:
            # Matches new event signature: VoteCast(address indexed voter, uint256 indexed candidateId)
            audit_trail.append({
                "voter": event.args.voter,
                "candidate_id": event.args.candidateId,
                "transaction_hash": event.transactionHash.hex(),
                "block_number": event.blockNumber
            })
        
        return audit_trail[::-1] # Return newest votes first
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []