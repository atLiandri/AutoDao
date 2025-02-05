import { axiosClient } from "../axios";

export const chat = (message) => {
    return axiosClient.post('/chat', {
        'message': message
    })
}