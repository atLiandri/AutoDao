// SPDX-License-Identifier: MIT
/*
    second version, added createTransactionProposal and createAddMembersProposal 
*/
pragma solidity ^0.8.19;

contract SimpleDAO {

    uint16 public proposalCount = 0;
    uint public memberCount = 1;   // creator is member
    uint64 constant ONE_DAY = 86400;

    mapping(address => bool) public members;
    mapping(uint256 => Proposal) public proposals;

    struct ProposalParameters {
        uint16 minApprovals;
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

    event ProposalCreated(uint id, address proposer);
    event Voted(uint id, address voter, uint voteCount);
    event ProposalExecuted(address actor, uint16 proposalId);

    modifier onlyMember() {
        require(members[msg.sender], "Not a DAO member");
        _;
    }

    modifier createProposal(uint16 _minApprovals, uint64 startDate, uint64 endDate) {
        
        if(startDate < block.timestamp){ // works also if startDate is not initialized
             startDate = uint64(block.timestamp);
        }

        if (endDate < block.timestamp){ // works also if endDate is not initialized
            endDate = startDate + 7*ONE_DAY;  // proposal lasts one week
        }
        
        Proposal storage newProposal = proposals[proposalCount];
        newProposal.proposer = msg.sender;
        newProposal.executed = false;
        newProposal.actionSuccess = false;
        newProposal.approvals = 0;
        newProposal.parameters.minApprovals = _minApprovals;
        _;
        unchecked {++ proposalCount;}
        emit ProposalCreated(proposalCount, msg.sender);
    }

    constructor() {
        members[msg.sender] = true;  // Initial creator is a member
    }


    function createTransactionProposal(uint16 _minApprovals, uint64 startDate, uint64 endDate, address _to, uint256 _value) 
        public  createProposal(_minApprovals, startDate, endDate) onlyMember {

        proposals[proposalCount].actionTo = _to;
        proposals[proposalCount].actionValue = _value;

    }

    function createAddMembersProposal(uint16 _minApprovals, uint64 startDate, uint64 endDate, address[] memory _newMembers) 
        public  createProposal(_minApprovals, startDate, endDate) onlyMember {

        proposals[proposalCount].membersToAdd = _newMembers;

    }  

    function voteOnProposal(uint16 _proposalId) public onlyMember {
        require(!proposals[_proposalId].approvers[msg.sender], "user already approved");

        require(!proposals[_proposalId].executed, "Proposal already executed");

        require(proposals[_proposalId].parameters.endDate <  uint64(block.timestamp), "Too late to vote");

        proposals[_proposalId].approvals++;
        proposals[_proposalId].approvers[msg.sender] = true;

        emit Voted(_proposalId, msg.sender, proposals[_proposalId].approvals);

        if(proposals[_proposalId].approvals >= proposals[_proposalId].parameters.minApprovals){ //add option to run this by backend if end date is reached
                _executeProposal(_proposalId); 
        }
    }


    function _executeProposal(uint16 _proposalId) internal {
        
        // add possibility to execute multiple actions?
        address[] memory membersToAdd = proposals[_proposalId].membersToAdd;
        if (membersToAdd.length!=0){
            _addNewMembers(membersToAdd);
        }
        uint256 actionValue = proposals[_proposalId].actionValue;
        address payable actionTo = payable(proposals[_proposalId].actionTo);
        if (actionTo!=address(0) && actionValue!=0){
            actionTo.transfer(actionValue);
        }

        emit ProposalExecuted({  // add action to event?
            actor: msg.sender,
            proposalId: _proposalId
        });
        proposals[_proposalId].executed = true;

    }

    function _addNewMembers(address[] memory _newMembers) internal { // unused at the moment, will be modified to be callable via action 
        for (uint i = 0; i < _newMembers.length; i++) {
            if (!members[_newMembers[i]]){
                memberCount++;
            }
            members[_newMembers[i]] = true;
            
        }
    }

    // add a bunch of view functions

    function hasVoted(uint16 _proposalId, address _voter) public view returns(bool) {
        return proposals[_proposalId].approvers[_voter];
    }

    function approversOnProposal(uint16 _proposalId) public view returns(uint16) {
        return proposals[_proposalId].approvals;
    }

    function proposedBy(uint16 _proposalId) public view returns(address) {
        return proposals[_proposalId].proposer;
    }  

    function isExecuted(uint16 _proposalId) public view returns(bool){
        return  proposals[_proposalId].executed;
    }

    function isAMember(address _candidate) public view returns(bool){
        return members[_candidate];
    }

    // To receive Ether to the treasury
    receive() external payable {}
}