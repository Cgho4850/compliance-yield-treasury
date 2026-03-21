# ComplianceYieldTreasury

> **ERC-3643 Compliant Yield Treasury for AI Agents**  
> Synthesis Hackathon 2026 · Built by Alhassan Mohammed ([@dahlinomine](https://github.com/dahlinomine))

[![Tests](https://img.shields.io/badge/tests-9%2F9%20passing-brightgreen)](./test/ComplianceYieldTreasuryTest.t.sol)
[![Chain](https://img.shields.io/badge/chain-Base%20Mainnet-blue)](https://basescan.org/address/0x99FCC335f879DbcF3AdA1623A769C7a6B3883d3D)
[![Solidity](https://img.shields.io/badge/solidity-0.8.20-orange)](./src/ComplianceYieldTreasury.sol)

## 🔗 Deployed Contract

| Network | Address | Explorer |
|---------|---------|----------|
| **Base Mainnet** | `0x99FCC335f879DbcF3AdA1623A769C7a6B3883d3D` | [Basescan](https://basescan.org/address/0x99FCC335f879DbcF3AdA1623A769C7a6B3883d3D) |

**Deployment TX:** [0x9970dc69...](https://basescan.org/tx/0x9970dc69777de8e7f6bae7eecb8d09cda1141964c0324ee3dbe60d40c855229f)

---

## What Is This?

A DeFi primitive that solves a real problem: **AI agents need operating budgets, but giving an agent an unlimited wallet is a security nightmare.**

The solution: deposit wstETH (Lido's wrapped staked ETH). The principal is **structurally locked** at the contract level — no agent can ever touch it. Only the yield flows to the agent's spending wallet.

The agent earns its keep from yield alone.

### How It Works

```
Agent stakes wstETH
        ↓
ComplianceYieldTreasury.sol
        ↓
    [ERC-3643 compliance check] ← Is this agent verified?
    [ERC-8004 identity check]   ← Does this agent own its identity token?
        ↓
Aave v3 on Base (supply wstETH → earn aWSTETH yield)
        ↓
Yield only → Agent's Locus payment wallet (spending guardrails)
Principal → LOCKED FOREVER at contract level
```

### The Compliance Gate

Before any agent can stake, two checks must pass:

1. **ERC-3643 Identity Registry** — is this address verified under the compliance framework? (KYC/AML for institutional-grade deployments)
2. **ERC-8004 Agent Identity** — does this address own a valid onchain agent identity NFT?

Both checks are enforced onchain. Not a frontend check. Not an API check. **Enforced in Solidity.**

---

## Bounty Targets

| Partner | Track | Prize |
|---------|-------|-------|
| **Lido Finance** | Treasury primitive (principal-locked yield) | $3,000 |
| **Lido Finance** | MCP server for natural-language staking | $5,000 |
| **Lido Finance** | Vault monitoring agent | $1,500 |
| **Locus** | Agent payment rails with guardrails | $3,000 |
| **Protocol Labs** | ERC-8004 trust layer implementation | $4,000 |
| **Total** | | **$16,500** |

---

## Architecture

```
compliance-yield-treasury/
├── src/
│   ├── ComplianceYieldTreasury.sol    # Core contract
│   └── interfaces/
│       ├── IERC3643.sol               # Compliance registry interface
│       ├── IERC8004.sol               # Agent identity interface  
│       └── IDefi.sol                  # Aave v3 + wstETH interfaces
├── test/
│   └── ComplianceYieldTreasuryTest.t.sol  # 9/9 fork tests (Base mainnet)
mcp-server/
└── server.py                          # FastMCP server (7 tools)
scripts/
├── deploy.py                          # Deployment script
└── monitor.py                         # Vault monitoring agent
```

## Key Onchain Addresses (Base Mainnet)

| Contract | Address |
|----------|---------|
| ComplianceYieldTreasury | `0x99FCC335f879DbcF3AdA1623A769C7a6B3883d3D` |
| wstETH (Lido on Base) | `0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452` |
| Aave v3 Pool | `0xA238Dd80C259a72e81d7e4664a9801593F98d1c5` |
| aWSTETH receipt token | `0x99CBC45ea5bb7eF3a5BC08FB1B7E56bB2442Ef0D` |
| ERC-8004 IdentityRegistry | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
| Locus spending wallet | `0xCb99E647AAb7670eb08947126C8525285A965AD7` |

---

## MCP Server

The MCP server wraps the contract in 7 natural-language tools:

```python
# Any Claude/AI agent can use these without understanding Solidity
check_eligibility(agent_address, erc8004_agent_id)  # Am I allowed to stake?
stake_wsteth(amount, erc8004_agent_id, spending_wallet)  # Stake!
get_position(agent_address)  # What's my current yield?
harvest_yield()  # Claim yield to my Locus wallet
get_treasury_stats()  # How is the whole vault doing?
register_erc8004_agent(name, description)  # Register onchain identity
monitor_vault(agent_address)  # Plain-English vault health report
```

### Connect to Claude Desktop

```json
{
  "mcpServers": {
    "compliance-yield-treasury": {
      "command": "python",
      "args": ["/path/to/mcp-server/server.py"],
      "env": {
        "BASE_RPC_URL": "https://mainnet.base.org",
        "TREASURY_ADDRESS": "0x99FCC335f879DbcF3AdA1623A769C7a6B3883d3D",
        "PRIVATE_KEY": "your-key-here"
      }
    }
  }
}
```

---

## Tests

9/9 Foundry fork tests passing against **live Base mainnet** — real Aave deposits, real yield accrual.

```bash
cd compliance-yield-treasury
forge test --fork-url https://mainnet.base.org -vv
```

```
[PASS] test_AaveIntegrationRealBalance()
[PASS] test_CannotStakeTwice()
[PASS] test_CannotStakeWithInvalidSpendingWallet()
[PASS] test_CannotStakeZeroAmount()
[PASS] test_Deploy()
[PASS] test_EligibilityCheck()
[PASS] test_PrincipalCannotBeDirectlyWithdrawn()
[PASS] test_StakeAndVerifyAaveDeposit()
[PASS] test_YieldAccruesOverTime()

Suite result: ok. 9 passed; 0 failed; 0 skipped
```

---

## Why ERC-3643?

The compliance gate isn't decoration — it's the core insight.

Standard DeFi yields are permissionless. That's fine for humans, but institutions deploying AI agents need to know:
- Which agents are authorized to move funds?
- Is this agent operating under a known compliance framework?
- Can the operation be audited and attributed to a verified identity?

ERC-3643 (the T-REX standard) was built for exactly this. Pairing it with ERC-8004 agent identity creates a two-layer authorization: **compliance verification** (is this entity allowed?) + **agent identity** (is this entity who they say they are?).

The result: a yield treasury that institutional-grade compliance requires, deployed on a chain that makes it affordable.

---

## Monitoring Agent

```bash
# Single vault health report
python scripts/monitor.py --once

# Continuous monitoring (every 60s)
python scripts/monitor.py --watch

# Focus on specific agent
python scripts/monitor.py --address 0xYourAgentAddress
```

Sample output:
```
────────────────────────────────────────────────────────
  🏦 ComplianceYieldTreasury — Vault Report
  2026-03-21 07:12 UTC | Block #43644001
────────────────────────────────────────────────────────

  STATUS: 🟢 HEALTHY

  WHAT'S LOCKED:
  • 0.010000 wstETH in principal (structurally locked)
  • Supplied to Aave v3 on Base, earning 0.0041% APY
  • 0.009999 aWSTETH in Aave (principal + yield)

  WHAT'S EARNED:
  • 0.00000004 wstETH in accrued yield
  • Yield routes to: 0xCb99E647... (Locus spending wallet)
  • Agents can call harvestYield() to claim
```

---

## Built By

Alhassan Mohammed — RWA tokenization compliance specialist, ERC-3643 ecosystem.  
- GitHub: [@dahlinomine](https://github.com/dahlinomine)  
- LinkedIn: [Alhassan Mohammed](https://linkedin.com/in/alhassan-mohammed-erc3643)

*Built for The Synthesis Hackathon 2026.*
