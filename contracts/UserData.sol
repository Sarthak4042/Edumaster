// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UserData {
    struct User {
        string name;
        uint256 age;
    }

    mapping(address => User) public users;

    function setUser(string memory _name, uint256 _age) public {
        users[msg.sender] = User(_name, _age);
    }
}
