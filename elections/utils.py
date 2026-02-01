import os
import json
from pathlib import Path
from web3 import Web3
from django.conf import settings

# Path(__file__) is 'elections/utils.py'
# .parent is 'elections/'
# .parent.parent is the project root 'blockchain_voting_backend/'
BASE_DIR = Path(__file__).resolve().parent.parent

def get_voting_contract():
    # 1. Connect to Ganache
    # Updated to Port 7545 based on your Ganache UI screenshot
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
    
    # 2. Dynamic paths to your JSON files
    # Based on your explorer and config: blockchain/ folder
    config_path = BASE_DIR / "blockchain" / "contract_config.json"
    
    # Path Verification for Config
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    # 3. Load Contract Address from your shared contract_config.json
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    # Use the address from the JSON: "0xD218B44D5a20916f87C48b0DB130fBA300615De8"
    # Web3.to_checksum_address ensures the address is in the correct EIP-55 format
    contract_address = Web3.to_checksum_address(config_data["contract_address"])
    
    # 4. Load ABI from the path specified in your config or your explorer
    # Matches: blockchain/abi/AdvancedVotingSystem.json
    abi_path = BASE_DIR / "blockchain" / "abi" / "AdvancedVotingSystem.json"
    
    if not abi_path.exists():
        raise FileNotFoundError(f"ABI file not found at: {abi_path}")

    with open(abi_path, 'r') as f:
        contract_json = json.load(f)
        # Handle Truffle vs. Raw ABI format
        contract_abi = contract_json.get('abi') if isinstance(contract_json, dict) else contract_json

    # 5. Create and return the contract object
    return w3.eth.contract(address=contract_address, abi=contract_abi)