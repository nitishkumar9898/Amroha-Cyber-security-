import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const store = useAuthStore.getState();
      try {
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refreshToken: store.refreshToken,
        });
        store.setTokens(data.accessToken, data.refreshToken);
        if (error.config) {
          error.config.headers.Authorization = `Bearer ${data.accessToken}`;
          return axios(error.config);
        }
      } catch {
        store.logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export default api;
