import client from './client';

export const register = (data) => client.post('/api/register', data);
export const login = (data) => client.post('/api/login', data);
export const logout = () => client.post('/api/logout');
export const me = () => client.get('/api/me');
export const updateProfile = (data) => client.patch('/api/me', data);
