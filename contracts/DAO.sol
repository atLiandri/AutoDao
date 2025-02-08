// SPDX-License-Identifier: MIT
/*
    future improvements: 
        1. add possibility for the proposals to change or add other AIs to the contract
        2. better manage proposal type
        3. include startDate
*/
pragma solidity ^0.8.19;

contract SimpleDAO {

    uint16 public proposalCount = 0;
    uint public memberCount = 0;
    uint64 constant ONE_DAY = 86400;
    uint8 constant MAX_MEMBERS_TO_ADD = 3;
    address AIAddress;
    address adminAddress;

    mapping(address => bool) public members;
    mapping(uint256 => Proposal) public proposals;

    struct ProposalParameters {
        uint64 startDate;
        uint64 endDate;
    }
    
    struct Proposal {
        address proposer;
        bool executed;
        bool actionSuccess;
        uint16 approvals;
        ProposalParameters parameters;
        mapping(address => bool) approvers;
        uint256 actionValue;
        address actionTo;
        address[] membersToAdd;
    }

    event ProposalCreated(uint id, address proposer, uint64 startDate, uint64 endDate);
    event Voted(uint id, address voter, uint voteCount);
    event ProposalExecuted(address actor, uint16 proposalId, string actionType, bool success);
    event MembersAdded(address[] newMembers);

    modifier onlyMember() {
        require(members[msg.sender], "Not a member of this DAO");
        _;
    }

    modifier onlyAIorMember() {
        require(msg.sender==AIAddress || members[msg.sender], "You are not a member nor the artificial mind of this DAO");
        _;
    }

    modifier onlyAdmin() {
            require(msg.sender == adminAddress, "You are not the admin");
            _;
        }
    
    modifier createProposal(uint64 startDate, uint64 endDate) {
        (startDate, endDate) = _setProposalDates(startDate, endDate);        
        Proposal storage newProposal = proposals[proposalCount];
        newProposal.proposer = msg.sender;
        newProposal.executed = false;
        newProposal.actionSuccess = false;
        newProposal.approvals = 0;
        newProposal.parameters.startDate = startDate;
        newProposal.parameters.endDate = endDate;
        _;
        unchecked {++ proposalCount;}
        emit ProposalCreated(proposalCount, msg.sender, startDate, endDate);
    }

    constructor() {
        adminAddress = msg.sender;
        members[msg.sender] = true;  // Initial creator is a member
        ++memberCount;
    }

    function _setProposalDates(uint64 startDate, uint64 endDate) internal view returns (uint64, uint64) {
        if (startDate < block.timestamp) {
            startDate = uint64(block.timestamp);
        }
        if (endDate < block.timestamp) {
            endDate = startDate + 7 * ONE_DAY;
        }
        return (startDate, endDate);
    }

    function setAIAddress (address _AIAddress) public onlyAdmin {
        AIAddress = _AIAddress;
    }

    function setAdminAddress (address _adminAddress) public onlyAdmin {
        adminAddress = _adminAddress;
    }

    function createTransactionProposal(uint64 endDate, address _to, uint256 _value) 
        public  createProposal(0,endDate) onlyAIorMember {
        require(_to != address(0), "Invalid recipient address");
        require(_value <= address(this).balance, "Insufficient contract balance");

        proposals[proposalCount].actionTo = _to;
        proposals[proposalCount].actionValue = _value;

    }

    function createAddMembersProposal( uint64 endDate, address[] memory _newMembers) 
        public  createProposal(0, endDate) onlyMember {
        require(_newMembers.length <= MAX_MEMBERS_TO_ADD, "Too many members to add");
        for (uint i = 0; i < _newMembers.length; i++) {
            require(_newMembers[i] != address(0), "0 address is an invalid member address");
        }
        proposals[proposalCount].membersToAdd = _newMembers;

    }  

    function voteOnProposal(uint16 _proposalId) public onlyMember {
        require(!proposals[_proposalId].approvers[msg.sender], "user already approved");

        require(!proposals[_proposalId].executed, "Proposal already executed");

        require(
            proposals[_proposalId].parameters.startDate <= uint64(block.timestamp) &&
            proposals[_proposalId].parameters.endDate >= uint64(block.timestamp),
            "Voting is not allowed at this time"
        );

        unchecked{++proposals[_proposalId].approvals;}
        proposals[_proposalId].approvers[msg.sender] = true;

        emit Voted(_proposalId, msg.sender, proposals[_proposalId].approvals);

        if (proposals[_proposalId].approvals >= (memberCount + 1) / 2) { //if more than half of the current members voted
            _executeProposal(_proposalId);
        }
       
    }


    function _executeProposal(uint16 _proposalId) internal {
        address[] memory membersToAdd = proposals[_proposalId].membersToAdd;
        if (membersToAdd.length!=0){
            _addNewMembers(membersToAdd);
        }
        uint256 actionValue = proposals[_proposalId].actionValue;
        address payable actionTo = payable(proposals[_proposalId].actionTo);

        proposals[_proposalId].executed = true;
        bool _actionSuccess = false;
        if (actionTo!=address(0) && actionValue!=0){
            (_actionSuccess, ) = actionTo.call{value: actionValue}("");
            proposals[_proposalId].actionSuccess = _actionSuccess;
        }

        emit ProposalExecuted(msg.sender, _proposalId, membersToAdd.length > 0 ? "AddMembers" : "Transaction", _actionSuccess);

    }

    function _addNewMembers(address[] memory _newMembers) internal { // unused at the moment, will be modified to be callable via action 
        for (uint i = 0; i < _newMembers.length;) {
            if (!members[_newMembers[i]]){
                memberCount++;
            }
            members[_newMembers[i]] = true;
            unchecked {++i;}   
        }
        emit MembersAdded(_newMembers);
    }

    function halfRoundingUp(uint x) public pure returns (uint256) {
    return (x + 1) / 2;
}

    // add a bunch of view functions

    function hasVoted(uint16 _proposalId, address _voter) external view returns(bool) {
        return proposals[_proposalId].approvers[_voter];
    }

    function approversOnProposal(uint16 _proposalId) external view returns(uint16) {
        return proposals[_proposalId].approvals;
    }

    function proposedBy(uint16 _proposalId) external view returns(address) {
        return proposals[_proposalId].proposer;
    }  

    function isExecuted(uint16 _proposalId) external view returns(bool){
        return  proposals[_proposalId].executed;
    }

    function isAMember(address _candidate) external view returns(bool){
        return members[_candidate];
    }

    function getProposalActionTo(uint16 _proposalId) external view returns (address) {
    return proposals[_proposalId].actionTo;
    }

    function getProposalActionValue(uint16 _proposalId) external view returns (uint256) {
        return proposals[_proposalId].actionValue;
    }

    function getProposalMembersToAdd(uint16 _proposalId) external view returns (address[] memory) {
        return proposals[_proposalId].membersToAdd;
    }

    // To receive Ether to the treasury
    receive() external payable {}
}