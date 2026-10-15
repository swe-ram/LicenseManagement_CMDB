import apiClient from '../api/client';

export const loginWithCredentials = async (username, password) => {
  const response = await apiClient.post('/auth/login', { username, password });
  return response.data.user;
};

export const getCurrentSession = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data.user;
};

export const logoutFromSession = async () => {
  await apiClient.post('/auth/logout');
};
