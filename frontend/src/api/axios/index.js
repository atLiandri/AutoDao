import Axios from "axios";

let baseURL = 'https://autodao.onrender.com';
let backendURL = 'http://localhost:5000';

const axiosConfig = {
  baseURL: baseURL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  timeout: 30000,
};

const backendAxiosConfig = {
  baseURL: backendURL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  timeout: 30000,
};

const axiosClient = Axios.create(axiosConfig);
const backendAxiosClient = Axios.create(backendAxiosConfig);

export { axiosClient, backendAxiosClient };