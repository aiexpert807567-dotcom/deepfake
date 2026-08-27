import axios from 'axios';

// Public backend URL used by the deployed Vercel app.
// Vercel can override this with NEXT_PUBLIC_API_URL, but the production
// fallback must never be localhost.
const PRODUCTION_API_URL = 'https://ai-face-studio-backend-d56h.onrender.com';

const getBaseUrl = () => {
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
  timeout: 120000,
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
