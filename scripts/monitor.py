#!/usr/bin/env python3
"""
Monitoring Agent — ComplianceYieldTreasury
==========================================
Synthesis Hackathon 2026 — Lido Finance $1,500 bounty (monitoring agent)

This autonomous monitoring agent watches the ComplianceYieldTreasury vault,
explains vault health in plain English, and notifies when yield is available.

Runs every N blocks and produces human-readable reports.

Usage:
    python scripts/monitor.py --once          # Single report
    python scripts/monitor.py --watch         # Continuous monitoring
    python scripts/monitor.py --address 0x..  # Monitor specific agent
"""

import os
import sys
import time
import json
import argparse
from web3 import Web3
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
TREASURY_ADDRESS = os.getenv("TREASURY_ADDRESS")
LOCUS_WALLET = "0xCb99E647AAb7670eb08947126C8525285A965AD7"
WSTETH = "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452"
AWSTETH = "0x99CBC45ea5bb7eF3a5BC08FB1B7E56bB2442Ef0D"
AAVE_POOL = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
AGENT_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"

POLL_SECONDS = 60  # Check every 60 seconds

# ─── Web3 Setup ──────────────────────────────────────────────────────────────

w3 = Web3(Web3.HTTPProvider(BASE_RPC))

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "type": "function", "stateMutability": "view"},
]

AAVE_ABI = [
    {"inputs": [{"name": "asset", "type": "address"}], "name": "getReserveData",
     "outputs": [
         {"name": "configuration", "type": "uint256"},
         {"name": "liquidityIndex", "type": "uint128"},
         {"name": "currentLiquidityRate", "type": "uint128"},
         {"name": "variableBorrowIndex", "type": "uint128"},
         {"name": "currentVariableBorrowRate", "type": "uint128"},
         {"name": "currentStableBorrowRate", "type": "uint128"},
         {"name": "lastUpdateTimestamp", "type": "uint40"},
         {"name": "id", "type": "uint16"},
         {"name": "aTokenAddress", "type": "address"},
         {"name": "stableDebtTokenAddress", "type": "address"},
         {"name": "variableDebtTokenAddress", "type": "address"},
         {"name": "interestRateStrategyAddress", "type": "address"},
         {"name": "accruedToTreasury", "type": "uint128"},
         {"name": "unbacked", "type": "uint128"},
         {"name": "isolationModeTotalDebt", "type": "uint128"}
     ],
     "type": "function", "stateMutability": "view"}
]

# ─── Monitor Logic ────────────────────────────────────────────────────────────

def fetch_apy() -> float:
    """Get current wstETH APY on Aave v3 Base."""
    try:
        aave = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL), abi=AAVE_ABI)
        data = aave.functions.getReserveData(Web3.to_checksum_address(WSTETH)).call()
        # liquidityRate in ray (1e27) → APY %
        return (data[2] / 1e27) * 100
    except Exception as e:
        return 0.0

def fetch_treasury_state() -> dict:
    """Fetch current treasury state from onchain."""
    if not TREASURY_ADDRESS:
        return {"error": "TREASURY_ADDRESS not set"}
    
    try:
        # Load ABI
        abi_path = Path(__file__).parent.parent / "compliance-yield-treasury/out/ComplianceYieldTreasury.sol/ComplianceYieldTreasury.json"
        with open(abi_path) as f:
            abi = json.load(f)["abi"]
        
        treasury = w3.eth.contract(
            address=Web3.to_checksum_address(TREASURY_ADDRESS), abi=abi
        )
        
        total_principal = treasury.functions.totalPrincipalLocked().call()
        total_aave = treasury.functions.totalAaveBalance().call()
        agent_count = treasury.functions.getAgentCount().call()
        apy = fetch_apy()
        
        return {
            "block": w3.eth.block_number,
            "timestamp": int(time.time()),
            "total_principal_wei": total_principal,
            "total_aave_wei": total_aave,
            "yield_accrued_wei": max(0, total_aave - total_principal),
            "agent_count": agent_count,
            "apy": apy,
            "health": "healthy" if total_aave >= total_principal else "warning",
            "treasury_address": TREASURY_ADDRESS,
        }
    except Exception as e:
        return {"error": str(e), "block": w3.eth.block_number}

def format_report(state: dict, agent_address: str = None) -> str:
    """Format state into a plain-English report."""
    if "error" in state:
        return f"⚠️  Monitoring error: {state['error']}"
    
    ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(state['timestamp']))
    principal_eth = state['total_principal_wei'] / 1e18
    aave_eth = state['total_aave_wei'] / 1e18
    yield_eth = state['yield_accrued_wei'] / 1e18
    
    health_icon = "🟢" if state['health'] == 'healthy' else "🔴"
    
    lines = [
        f"",
        f"{'─'*52}",
        f"  🏦 ComplianceYieldTreasury — Vault Report",
        f"  {ts} | Block #{state['block']}",
        f"{'─'*52}",
        f"",
        f"  STATUS: {health_icon} {state['health'].upper()}",
        f"",
        f"  WHAT'S LOCKED:",
        f"  • {principal_eth:.6f} wstETH in principal (structurally locked)",
        f"  • Supplied to Aave v3 on Base, earning {state['apy']:.4f}% APY",
        f"  • {aave_eth:.6f} aWSTETH in Aave (principal + yield)",
        f"",
        f"  WHAT'S EARNED:",
        f"  • {yield_eth:.8f} wstETH in accrued yield",
        f"  • Yield routes to: {LOCUS_WALLET[:10]}... (Locus spending wallet)",
        f"  • Agents can call harvestYield() to claim",
        f"",
        f"  WHO'S IN THE VAULT:",
        f"  • {state['agent_count']} active AI agent(s) staked",
        f"  • Each verified via ERC-3643 (compliance) + ERC-8004 (identity)",
        f"",
        f"  HOW IT WORKS:",
        f"  • Agents stake wstETH → Aave earns yield",
        f"  • Principal: LOCKED at contract level (agents can't touch it)",
        f"  • Yield: flows to agent's Locus payment wallet autonomously",
        f"  • Locus enforces spending limits on the yield wallet",
        f"",
        f"  CONTRACT: {TREASURY_ADDRESS}",
        f"  BASESCAN: https://basescan.org/address/{TREASURY_ADDRESS}",
        f"{'─'*52}",
    ]
    
    return "\n".join(lines)

def run_monitor(watch: bool = False, agent_address: str = None, interval: int = POLL_SECONDS):
    """Run the monitoring agent."""
    print("🤖 ComplianceYieldTreasury Monitoring Agent")
    print(f"   Treasury: {TREASURY_ADDRESS or '⚠️  NOT SET'}")
    print(f"   Chain: Base mainnet")
    print(f"   RPC: {BASE_RPC}")
    print()
    
    iterations = 0
    while True:
        iterations += 1
        state = fetch_treasury_state()
        report = format_report(state, agent_address)
        print(report)
        
        # Save to log
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / "monitor_log.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps(state) + "\n")
        
        if not watch:
            break
        
        print(f"\n  ⏱  Next check in {interval}s... (Ctrl+C to stop)\n")
        time.sleep(interval)

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ComplianceYieldTreasury Monitoring Agent")
    parser.add_argument("--once", action="store_true", default=True, help="Single report (default)")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--address", help="Focus on specific agent address")
    parser.add_argument("--interval", type=int, default=POLL_SECONDS)
    args = parser.parse_args()
    
    run_monitor(
        watch=args.watch,
        agent_address=args.address,
        interval=args.interval
    )
