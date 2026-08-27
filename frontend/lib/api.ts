import axios from 'axios';

const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // If in GitHub Codespaces, automatically switch from port 3000 URL to port 8000 URL
    if (window.location.hostname.includes('-3000.')) {
      return window.location.origin.replace('-3000.', '-8000.');
    }
    return 'http://localhost:8000';
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export const apiClient = axios.create({
  baseURL: getBaseUrl(),
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    config.baseURL = getBaseUrl();
    const token = localStorage.getItem('studio_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
