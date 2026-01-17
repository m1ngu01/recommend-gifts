import axios from "axios";

const baseURL =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

const API_TIMEOUT =
  Number((import.meta as any).env?.VITE_API_TIMEOUT_MS) ||
  60000; // 무거운 추천 계산 대비 여유 시간

const client = axios.create({
  baseURL,
  withCredentials: true,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      if (location.pathname !== "/login") {
        location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

export default client;
