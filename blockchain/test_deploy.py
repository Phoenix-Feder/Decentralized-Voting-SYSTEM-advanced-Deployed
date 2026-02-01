import json
import time
from web3_config import deploy_election, get_voting_contract, w3, PRIVATE_KEY, ADMIN_ADDRESS

# 1. Election Configuration
ELECTION_NAME = "Main Campus Election 2026"
DURATION_MINS = 120  # 2 hours

print(f"🛰️ Starting deployment for: {ELECTION_NAME}")

# 2. Deploy the Contract (Empty Constructor)
address = deploy_election()

if address:
    print(f"✅ Contract deployed at: {address}")

    # 3. SAVE TO CONFIG IMMEDIATELY
    config = {
        "contract_address": address,
        "abi_path": "blockchain/abi/AdvancedVotingSystem.json"
    }
    with open("contract_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("📦 contract_config.json updated.")

    # Small delay to let the blockchain settle
    time.sleep(1)

    # 4. INITIALIZE ELECTION (Now with Start and End Timestamps)
    try:
        print("🔧 Initializing election settings on-chain...")
        contract = get_voting_contract()
        
        # Calculate Unix Timestamps for the new contract logic
        start_ts = int(time.time())             # Start now
        end_ts = start_ts + (DURATION_MINS * 60) # End in X minutes
        
        nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)
        
        # UPDATED: Passing 3 arguments to setupElection
        setup_tx = contract.functions.setupElection(
            ELECTION_NAME, 
            start_ts,
            end_ts
        ).build_transaction({
            'from': ADMIN_ADDRESS,
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': w3.to_wei('2', 'gwei'),
            'chainId': w3.eth.chain_id
        })

        # Sign and Send using .raw_transaction
        signed_tx = w3.eth.account.sign_transaction(setup_tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"⏳ Waiting for initialization receipt...")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"🎊 Election Initialized! Tx Hash: {tx_hash.hex()}")
        print(f"📍 Settings: Name='{ELECTION_NAME}', Start={start_ts}, End={end_ts}")
        
    except Exception as e:
        print(f"⚠️ Deployment succeeded, but initialization failed: {e}")
else:
    print("❌ Deployment failed. Is Ganache running?")