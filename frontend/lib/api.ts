import axios from 'axios';
import { DashboardData } from '../types/dashboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8095';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const getDashboardData = async (): Promise<DashboardData> => {
  const response = await api.get<DashboardData>('/api/dashboard');
  return response.data;
};

export const getUserPreference = async () => {
  const response = await api.get('/api/user_preference');
  return response.data;
};

export const updateUserPreference = async (preference: string) => {
  const response = await api.post('/api/user_preference', { tea_frequency: preference });
  return response.data;
};

export const startIndexingAllRepos = async () => {
  const endDate = new Date();
  const startDate = new Date(endDate);
  startDate.setDate(startDate.getDate() - 1); // Index last 2 days

  const response = await api.post('/api/index-all-repos', {
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString(),
  });
  return response.data;
}
