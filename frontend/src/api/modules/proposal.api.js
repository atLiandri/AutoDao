import { backendAxiosClient } from "../axios";

export const proposals = () => {
    return backendAxiosClient.get('/api/proposals');
}

export const proposal = (message) => {
    return backendAxiosClient.post('/api/proposals', message);
}