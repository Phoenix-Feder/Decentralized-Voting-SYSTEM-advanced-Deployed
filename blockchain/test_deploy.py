import json
import time
from web3_config import deploy_election

now = int(time.time())

address = deploy_election(
    start_time=now + 60,
    end_time=now + 3600
)

print("✅ Contract deployed at:", address)

# ---- SAVE ADDRESS AUTOMATICALLY ----
config = {
    "contract_address": address,
    "abi_path": "blockchain/abi/AdvancedVotingSystem.json"
}

with open("contract_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("📦 Saved to contract_config.json")
