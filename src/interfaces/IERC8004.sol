// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IERC8004 Agent Identity Registry
 * @dev Interface for ERC-8004 onchain AI agent identity registry
 * @notice Deployed on Base at 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432
 */
interface IAgentIdentityRegistry {
    struct AgentMetadata {
        string name;
        string agentURI;  // IPFS URI pointing to agent registration JSON
        bool active;
        uint256 registeredAt;
        address owner;
    }

    /// @notice Register a new agent, returns the agent tokenId
    function register(string calldata agentURI, bytes calldata metadata) 
        external returns (uint256 agentId);

    /// @notice Check if a tokenId is registered
    function isRegistered(uint256 agentId) external view returns (bool);

    /// @notice Get the owner of an agent identity
    function ownerOf(uint256 tokenId) external view returns (address);

    /// @notice Get agent URI for a tokenId
    function tokenURI(uint256 tokenId) external view returns (string memory);

    /// @notice Name of the registry NFT
    function name() external view returns (string memory);

    /// @notice Symbol of the registry NFT  
    function symbol() external view returns (string memory);

    /// @notice Check if address owns at least one agent identity token
    function balanceOf(address owner) external view returns (uint256);
}

interface IAgentReputationRegistry {
    struct Feedback {
        int128 value;        // Signed integer rating
        uint8 valueDecimals; // 0-18 decimal places  
        string tag1;         // E.g., "uptime"
        string tag2;         // E.g., "30days"
        string endpoint;     // Agent endpoint URI
        string ipfsHash;     // Optional metadata
        bytes32 dataHash;    // Hash of underlying data
    }

    /// @notice Submit feedback for an agent
    function giveFeedback(
        uint256 agentId,
        int128 value,
        uint8 valueDecimals,
        string calldata tag1,
        string calldata tag2,
        string calldata endpoint,
        string calldata ipfsHash,
        bytes32 dataHash
    ) external;

    /// @notice Get aggregate reputation summary
    function getSummary(
        uint256 agentId,
        address[] calldata trustedClients,
        string calldata tag1,
        string calldata tag2
    ) external view returns (uint64 count, int128 value, uint8 decimals);
}
