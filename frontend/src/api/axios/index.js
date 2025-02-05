import Axios from "axios";

let baseURL = 'https://agentblockchainhackathon.onrender.com';

const axiosConfig = {
  baseURL: baseURL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  timeout: 30000,
};

const axiosClient = Axios.create(axiosConfig);

export { axiosClient };