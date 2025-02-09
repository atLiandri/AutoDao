import { ChatApi } from "@/api";

export const chat = async (message) => {
    const { data } = await ChatApi.chat(message);
    return data;
}