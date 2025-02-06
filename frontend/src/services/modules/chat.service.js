import { ChatApi } from "@/api";

export const chat = async (message) => {
    const { data } = await ChatApi.chat(message);
    return data;
}

export const create_proposal = async (message) => {
    const { data } = await ChatApi.create_proposal(message);
    return data;
}