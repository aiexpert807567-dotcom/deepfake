import axios from 'axios';
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const apiClient = axios.create({ baseURL: API_BASE });
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('studio_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
