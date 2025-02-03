// SPDX-License-Identifier: MIT
/*
    first version, currently basically nothing has been tested
*/
pragma solidity ^0.8.19;

contract SimpleDAO {

    uint16 public proposalCount = 0;
    uint public memberCount = 1;

    mapping(address => bool) public members;
    mapping(uint256 => Proposal) public proposals;

    struct Action {
        address to;
        uint256 value;
        bytes data;
    }

    struct ProposalParameters {
        uint16 minApprovals;
        uint64 startDate;
        uint64 endDate;
    }

    struct Proposal {
        bool executed;
        bool actionSuccess;
        uint16 approvals;
        ProposalParameters parameters;
        mapping(address => bool) approvers;
        Action action;
        address proposer;
    }

    event ProposalCreated(uint id, address proposer);
    event Voted(uint id, address voter, uint voteCount);
    event ProposalExecuted(address actor, uint16 proposalId, bytes execResult);

    modifier onlyMember() {
        require(members[msg.sender], "Not a DAO member");
        _;
    }

    constructor() {
        members[msg.sender] = true;  // Initial creator is a member
    }

    function createProposal(uint16 _minApprovals, address _actionTo, uint256 _actionValue, bytes calldata _actionData) 
        public onlyMember {

        // add check to ensure last block in which a modification has happend has already been mined

        // add check start and end date are inside bounds, else revert

        // add set start & end date in proposalParameters

        Proposal storage newProposal = proposals[proposalCount];
        newProposal.proposer = msg.sender;
        newProposal.action.to =  _actionTo;
        newProposal.action.value =  _actionValue;
        newProposal.action.data =  _actionData;
        newProposal.parameters.minApprovals = _minApprovals;
        newProposal.executed = false;
        newProposal.actionSuccess = false;
        newProposal.approvals = 0;

        unchecked {++ proposalCount;}
        emit ProposalCreated(proposalCount, msg.sender);
    }

    function voteOnProposal(uint16 _proposalId) public onlyMember {
        require(!proposals[_proposalId].approvers[msg.sender], "user already approved");

        require(!proposals[_proposalId].executed, "Proposal already executed");

        require(proposals[_proposalId].parameters.endDate <  uint64(block.timestamp));

        proposals[_proposalId].approvals++;
        proposals[_proposalId].approvers[msg.sender] = true;

        emit Voted(_proposalId, msg.sender, proposals[_proposalId].approvals);

        if(proposals[_proposalId].approvals >= proposals[_proposalId].parameters.minApprovals){ //add option to run this by backend if end date is reached
            _executeProposal(_proposalId, proposals[_proposalId].action); 
        }
    }

    function _executeProposal(uint16 _proposalId, Action memory _action) internal returns(bytes memory){
        
        // add possibility to execute multiple actions?

        (bool success, bytes memory execResult) = _action.to.call{value: _action.value}(
            _action.data
        );

        emit ProposalExecuted({  // add action to event?
            actor: msg.sender,
            proposalId: _proposalId,
            execResult: execResult
        });
        proposals[_proposalId].actionSuccess = success;
        proposals[_proposalId].executed = true;

        return execResult;  // unused at the moment
    }

    function _addNewMember(address[] memory _newMembers) internal { // unused at the moment, will be modified to be callable via action 
        for (uint i = 0; i < _newMembers.length; i++) {
            require(!members[_newMembers[i]], "Address is already a member");
            members[_newMembers[i]] = true;
            memberCount++;
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