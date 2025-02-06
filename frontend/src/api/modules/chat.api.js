import { axiosClient } from "../axios";

export const chat = (message) => {
    return axiosClient.post('/chat', {
        'message': message
    })
}

export const create_proposal = (parsed_content) => {
    return axiosClient.post('/create_proposal', {
        'parsed_content': parsed_content
    })
}