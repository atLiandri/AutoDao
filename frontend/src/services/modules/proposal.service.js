import { ProposalApi } from "@/api";

export const getProposals = async () => {
    const { data } = await ProposalApi.proposals();
    return data;
}