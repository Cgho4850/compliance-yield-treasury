// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IERC3643 Compliance Registry Interface
 * @dev Simplified interface for ERC-3643 identity compliance checking
 * @notice Agents must be verified in an ERC-3643 Identity Registry to interact
 */
interface IIdentityRegistry {
    /// @notice Check if an address has a verified identity registered
    function isVerified(address _userAddress) external view returns (bool);
    
    /// @notice Check if an address is registered (may not be verified)
    function contains(address _userAddress) external view returns (bool);
    
    /// @notice Get the identity contract for an address
    function identity(address _userAddress) external view returns (address);
    
    /// @notice Get the country code for an address
    function investorCountry(address _userAddress) external view returns (uint16);
}

interface ICompliance {
    /// @notice Check if a transfer is compliant
    function canTransfer(address _from, address _to, uint256 _amount) external view returns (bool);
    
    /// @notice Check if a token can be added to a compliance module
    function isTokenAgent(address _agentAddress) external view returns (bool);
}
