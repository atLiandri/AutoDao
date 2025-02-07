import { axiosClient } from "../axios";

export const proposals = () => {
    return axiosClient.get('/proposals')
}