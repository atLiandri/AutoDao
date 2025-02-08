import { ProposalApi } from "@/api";

export const getProposals = async () => {
    const { data } = await ProposalApi.proposals();
    return data;
}

export const postProposal = async (message) => {
    const { data } = await ProposalApi.proposal(message);
    return data;
}