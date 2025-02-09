import { ProposalApi } from "@/api";

export const getProposals = async () => {
    const { data } = await ProposalApi.proposals();
    return data;
}

export const postProposal = async (proposal) => {
    const { data } = await ProposalApi.proposal(proposal);
    return data;
}