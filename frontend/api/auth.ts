import request from './request'

export const authApi = {
  login: (data: LoginRequest): Promise<LoginResponse> =>
    request.post('/auth/login', data),

  logout: (): Promise<void> =>
    request.post('/auth/logout'),

  getCurrentUser: (): Promise<User> =>
    request.get('/auth/me'),
}