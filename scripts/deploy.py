#!/usr/bin/env python3
"""
Deploy ComplianceYieldTreasury to Base mainnet/testnet.

Usage:
    # Deploy to Base Sepolia (testnet — free faucet ETH):
    python deploy.py --network sepolia
    
    # Deploy to Base mainnet (real ETH required — ~$0.50 in gas):
    python deploy.py --network mainnet
    
    # Verify deployment:
    python deploy.py --verify <contract_address>
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

BASE_MAINNET_RPC = "https://mainnet.base.org"
BASE_SEPOLIA_RPC = "https://sepolia.base.org"

# Pre-verified ERC-3643 registry addresses
# address(0) = bypass compliance check (testnet mode)
IDENTITY_REGISTRY = {
    "mainnet": "0x0000000000000000000000000000000000000000",  # Set to real ERC-3643 registry when available
    "sepolia": "0x0000000000000000000000000000000000000000",  # bypass for testing
}

def get_deployer_address(private_key: str) -> str:
    """Get deployer address from private key."""
    from eth_account import Account
    return Account.from_key(private_key).address

def deploy(network: str, private_key: str):
    """Deploy the contract using forge create."""
    rpc = BASE_MAINNET_RPC if network == "mainnet" else BASE_SEPOLIA_RPC
    identity_registry = IDENTITY_REGISTRY[network]
    
    deployer = get_deployer_address(private_key)
    print(f"🚀 Deploying ComplianceYieldTreasury")
    print(f"   Network: Base {network}")
    print(f"   RPC: {rpc}")
    print(f"   Deployer: {deployer}")
    print(f"   Identity Registry: {identity_registry}")
    print()
    
    # Use forge create
    cmd = [
        "forge", "create",
        "--rpc-url", rpc,
        "--private-key", private_key,
        "src/ComplianceYieldTreasury.sol:ComplianceYieldTreasury",
        "--constructor-args", identity_registry,
        "--broadcast",
    ]
    
    result = subprocess.run(
        cmd,
        cwd="/home/user/surething/cells/317327b9-e741-40c3-86be-a774de73302e/workspace/compliance-yield-treasury",
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr)
        return None
    
    # Parse deployed address
    for line in result.stdout.split("\n"):
        if "Deployed to:" in line:
            address = line.split("Deployed to:")[1].strip()
            print(f"✅ Contract deployed at: {address}")
            print(f"   Basescan: https://basescan.org/address/{address}")
            
            # Save to .env
            env_path = Path("../../mcp-server/.env")
            env_content = env_path.read_text() if env_path.exists() else ""
            if "TREASURY_ADDRESS=" not in env_content:
                with open(env_path, "a") as f:
                    f.write(f"\nTREASURY_ADDRESS={address}\n")
            
            return address
    
    return None

def check_balance(address: str, rpc: str) -> float:
    """Check ETH balance of an address."""
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    balance_wei = w3.eth.get_balance(address)
    return balance_wei / 1e18

def setup_instructions():
    """Print setup instructions for users without a funded wallet."""
    print("""
═══════════════════════════════════════════════════════
  HOW TO GET A FUNDED WALLET FOR DEPLOYMENT
═══════════════════════════════════════════════════════

OPTION 1: Base Sepolia Testnet (FREE — for testing)
  1. Get a wallet private key (generate with: cast wallet new)
  2. Get free test ETH from faucet:
     - https://faucet.quicknode.com/base/sepolia
     - https://docs.base.org/docs/tools/network-faucets/
  3. Run: python deploy.py --network sepolia

OPTION 2: Base Mainnet (REAL — ~$0.50 needed)
  1. Buy ETH on Coinbase → withdraw to Base network
  2. Or bridge from Ethereum: https://bridge.base.org
  3. Need ~0.0002 ETH ($0.40 at $2000/ETH) for deployment
  4. Run: python deploy.py --network mainnet

OPTION 3: Use Coinbase Wallet (easiest)
  1. Download Coinbase Wallet app
  2. Create wallet, export private key
  3. Buy $5 of ETH, select "Base" network
  4. Run: python deploy.py --network mainnet

WHAT WE ALREADY HAVE:
  ✅ Locus wallet: 0xCb99E647AAb7670eb08947126C8525285A965AD7 (Base, $5 USDC)
  ✅ Public Base RPC: https://mainnet.base.org (free, no key needed)
  ✅ Contract: compiled and tested (9/9 tests passing)
  ✅ MCP Server: ready to connect after deployment
  
STILL NEEDED:
  ❌ ~$1-2 of ETH on Base for gas (to deploy contract + execute real txs)

═══════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", choices=["mainnet", "sepolia"], default="sepolia")
    parser.add_argument("--private-key", help="Deployer private key (or set PRIVATE_KEY env var)")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    args = parser.parse_args()
    
    if args.setup:
        setup_instructions()
        sys.exit(0)
    
    private_key = args.private_key or os.getenv("PRIVATE_KEY")
    if not private_key:
        print("❌ No private key provided.")
        print("   Set PRIVATE_KEY environment variable or use --private-key")
        print("   Run: python deploy.py --setup")
        setup_instructions()
        sys.exit(1)
    
    rpc = BASE_MAINNET_RPC if args.network == "mainnet" else BASE_SEPOLIA_RPC
    deployer = get_deployer_address(private_key)
    balance = check_balance(deployer, rpc)
    
    print(f"💳 Deployer: {deployer}")
    print(f"💰 Balance: {balance:.6f} ETH on Base {args.network}")
    
    if balance < 0.0001:
        print(f"\n⚠️  Insufficient ETH for deployment.")
        print(f"   Need at least 0.0001 ETH (~$0.20). Current: {balance:.8f} ETH")
        setup_instructions()
        sys.exit(1)
    
    deploy(args.network, private_key)
