// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract LoyaltyToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    bytes32 public constant PARTNER_ROLE = keccak256("PARTNER_ROLE");

    event LoyaltyMinted(address indexed partner, address indexed customer, uint256 amount, string reference);
    event LoyaltyRedeemed(address indexed partner, address indexed customer, uint256 amount, string reference);

    constructor() ERC20("Universal Loyalty Point", "ULP") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(BURNER_ROLE, msg.sender);
        _grantRole(PARTNER_ROLE, msg.sender);
    }

    function mint(address to, uint256 amount, string memory reference) external onlyRole(MINTER_ROLE) {
        require(amount > 0, "amount must be positive");
        _mint(to, amount);
        emit LoyaltyMinted(msg.sender, to, amount, reference);
    }

    function burn(address from, uint256 amount, string memory reference) external onlyRole(BURNER_ROLE) {
        require(amount > 0, "amount must be positive");
        _burn(from, amount);
        emit LoyaltyRedeemed(msg.sender, from, amount, reference);
    }

    function transfer(address to, uint256 amount) public override returns (bool) {
        require(amount > 0, "amount must be positive");
        return super.transfer(to, amount);
    }

    function balanceOf(address account) public view override returns (uint256) {
        return super.balanceOf(account);
    }
}
