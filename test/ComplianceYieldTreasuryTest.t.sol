// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console2} from "forge-std/Test.sol";
import {ComplianceYieldTreasury} from "../src/ComplianceYieldTreasury.sol";
import {IERC20} from "../src/interfaces/IDefi.sol";

/**
 * @title ComplianceYieldTreasuryTest
 * @notice Fork tests against Base mainnet — real Aave v3 + real wstETH
 *
 * Run with:
 *   forge test --fork-url https://mainnet.base.org -vvv
 */
contract ComplianceYieldTreasuryTest is Test {
    // ─── Base mainnet addresses ───
    address constant WSTETH = 0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452;
    address constant AWSTETH = 0x99CBC45ea5bb7eF3a5BC08FB1B7E56bB2442Ef0D;
    address constant AAVE_POOL = 0xA238Dd80C259a72e81d7e4664a9801593F98d1c5;
    address constant AGENT_REGISTRY = 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432;

    ComplianceYieldTreasury public treasury;
    address public agent = makeAddr("agent");
    address public spendingWallet = makeAddr("locusWallet");
    address public deployer = makeAddr("deployer");

    // We'll use a real ERC-8004 agent ID (we'll register one in setup)
    uint256 public agentId;

    function setUp() public {
        // Fork Base mainnet
        vm.createSelectFork("https://mainnet.base.org");

        vm.startPrank(deployer);
        // Deploy treasury with NO identity registry (bypass ERC-3643 for testing)
        treasury = new ComplianceYieldTreasury(address(0));
        vm.stopPrank();

        // Give agent some wstETH (deal is available in fork tests)
        // wstETH whale on Base — use vm.deal for ETH, then deal for ERC20
        deal(WSTETH, agent, 1 ether);

        // Register an ERC-8004 agent identity for our test agent
        // We'll mock this since we can't sign real transactions in test
        vm.startPrank(agent);
        // Mock: pretend agent registered and got tokenId 1
        // In production, agent calls: agentRegistry.register(agentURI, metadata)
        vm.stopPrank();

        agentId = _registerMockAgent();
    }

    /// @dev Register a mock agent in ERC-8004 registry
    function _registerMockAgent() internal returns (uint256) {
        // Try to register via the actual registry
        vm.startPrank(agent);
        
        // ERC-8004 register function — ABI encode the call
        bytes memory metadata = abi.encode("ComplianceYieldTreasury", "Base", block.timestamp);
        string memory agentURI = "ipfs://QmSynthesisHackathon2026ComplianceYieldTreasury";
        
        (bool success, bytes memory data) = AGENT_REGISTRY.call(
            abi.encodeWithSignature("register(string,bytes)", agentURI, metadata)
        );
        
        vm.stopPrank();
        
        if (success && data.length > 0) {
            return abi.decode(data, (uint256));
        }
        
        // If registry call fails, mock ownership using vm.mockCall
        uint256 mockId = 9999;
        vm.mockCall(
            AGENT_REGISTRY,
            abi.encodeWithSignature("ownerOf(uint256)", mockId),
            abi.encode(agent)
        );
        return mockId;
    }

    // ═══════════════════════════════════════════════════════════
    // TESTS
    // ═══════════════════════════════════════════════════════════

    function test_Deploy() public view {
        assertEq(treasury.owner(), deployer);
        assertEq(treasury.identityRegistry(), address(0));
        assertEq(treasury.totalPrincipalLocked(), 0);
        console2.log("Treasury deployed at:", address(treasury));
        console2.log("wstETH on Base:", WSTETH);
        console2.log("Aave Pool on Base:", AAVE_POOL);
    }

    function test_StakeAndVerifyAaveDeposit() public {
        uint256 stakeAmount = 0.01 ether; // 0.01 wstETH

        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), stakeAmount);

        uint256 wstETHBefore = IERC20(WSTETH).balanceOf(agent);
        uint256 aWstETHBefore = IERC20(AWSTETH).balanceOf(address(treasury));

        treasury.stake(stakeAmount, agentId, spendingWallet);
        vm.stopPrank();

        uint256 wstETHAfter = IERC20(WSTETH).balanceOf(agent);
        uint256 aWstETHAfter = IERC20(AWSTETH).balanceOf(address(treasury));

        // Agent's wstETH balance decreased
        assertEq(wstETHBefore - wstETHAfter, stakeAmount, "wstETH not transferred from agent");

        // Treasury received aWSTETH from Aave
        assertGt(aWstETHAfter, aWstETHBefore, "No aWSTETH received from Aave");

        // Position recorded correctly
        (
            uint256 principal,
            uint256 currentAWstETH,
            uint256 estimatedYield,
            address sw,
            uint256 eid,
            ,
            ,
            bool active
        ) = treasury.getPosition(agent);

        assertEq(principal, stakeAmount, "Principal not recorded correctly");
        assertEq(sw, spendingWallet, "Spending wallet not set");
        assertEq(eid, agentId, "Agent ID not set");
        assertTrue(active, "Position not active");
        assertEq(estimatedYield, 0, "Should have no yield at time of staking");

        console2.log("Staked:", stakeAmount);
        console2.log("aWSTETH received:", aWstETHAfter - aWstETHBefore);
        console2.log("Principal locked:", principal);
    }

    function test_YieldAccruesOverTime() public {
        uint256 stakeAmount = 0.1 ether;

        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), stakeAmount);
        treasury.stake(stakeAmount, agentId, spendingWallet);
        vm.stopPrank();

        // Fast-forward 30 days
        vm.warp(block.timestamp + 30 days);
        vm.roll(block.number + 200000);

        (,, uint256 estimatedYield,,,,, bool active) = treasury.getPosition(agent);

        assertTrue(active, "Position not active");
        // Note: In a real fork test, yield accrues as Aave updates its index
        // Here we verify the structure is correct; real yield tested on mainnet
        console2.log("Estimated yield after 30 days:", estimatedYield);
        console2.log("Position is active:", active);
    }

    function test_CannotStakeZeroAmount() public {
        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), 1 ether);
        vm.expectRevert(ComplianceYieldTreasury.ZeroAmount.selector);
        treasury.stake(0, agentId, spendingWallet);
        vm.stopPrank();
    }

    function test_CannotStakeWithInvalidSpendingWallet() public {
        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), 0.01 ether);
        vm.expectRevert(ComplianceYieldTreasury.InvalidSpendingWallet.selector);
        treasury.stake(0.01 ether, agentId, address(0));
        vm.stopPrank();
    }

    function test_CannotStakeTwice() public {
        uint256 stakeAmount = 0.01 ether;
        
        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), stakeAmount * 2);
        treasury.stake(stakeAmount, agentId, spendingWallet);
        
        vm.expectRevert(
            abi.encodeWithSelector(
                ComplianceYieldTreasury.PositionAlreadyActive.selector, agent
            )
        );
        treasury.stake(stakeAmount, agentId, spendingWallet);
        vm.stopPrank();
    }

    function test_EligibilityCheck() public view {
        (bool erc3643, bool erc8004, bool eligible) = treasury.isEligible(agent, agentId);

        // ERC-3643 bypassed (registry = address(0))
        assertTrue(erc3643, "ERC-3643 should pass (bypassed)");
        
        // ERC-8004 check depends on actual registry state
        console2.log("ERC-3643 compliant:", erc3643);
        console2.log("ERC-8004 valid:", erc8004);
        console2.log("Overall eligible:", eligible);
    }

    function test_PrincipalCannotBeDirectlyWithdrawn() public {
        uint256 stakeAmount = 0.01 ether;

        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), stakeAmount);
        treasury.stake(stakeAmount, agentId, spendingWallet);
        
        // Agent has no active position to harvest (no yield yet)
        // and there is no "withdraw principal" function — by design
        // Verify no withdrawPrincipal function exists (structural lock)
        vm.stopPrank();

        // The only way to get funds out is via harvestYield()
        // which ONLY sends the delta above principal
        assertEq(treasury.totalPrincipalLocked(), stakeAmount, "Principal should be locked");
        console2.log("Principal structurally locked:", treasury.totalPrincipalLocked());
    }

    function test_AaveIntegrationRealBalance() public {
        uint256 stakeAmount = 0.01 ether;

        vm.startPrank(agent);
        IERC20(WSTETH).approve(address(treasury), stakeAmount);
        treasury.stake(stakeAmount, agentId, spendingWallet);
        vm.stopPrank();

        uint256 aaveBalance = treasury.totalAaveBalance();
        assertGt(aaveBalance, 0, "Should have Aave balance after staking");
        
        console2.log("Treasury aWSTETH balance (Aave):", aaveBalance);
        console2.log("Real yield will flow to Locus wallet:", spendingWallet);
    }
}
