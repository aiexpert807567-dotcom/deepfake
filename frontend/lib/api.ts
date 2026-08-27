import axios from 'axios';

// Single source of truth for the deployed API URL.
export const PRODUCTION_API_URL = 'https://ai-face-studio-backend-d56h.onrender.com';

export const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const configured = process.env.NEXT_PUBLIC_API_URL;
    if (configured) return configured.replace(/\/$/, '');

    if (window.location.hostname.includes('-3000.')) {
      return window.location.origin.replace('-3000.', '-8000.');
    }

    return PRODUCTION_API_URL;
  }

  return (process.env.NEXT_PUBLIC_API_URL || PRODUCTION_API_URL).replace(/\/$/, '');
};

export const apiClient = axios.create({
  baseURL: getBaseUrl(),
  // Render can cold-start. Uploads can also take longer than 2 minutes.
  timeout: 10 * 60 * 1000,
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('studio_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined' && error.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('studio_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
