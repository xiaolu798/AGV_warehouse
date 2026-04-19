import request from './request'

export const loginApi = (payload) => request.post('/user/login', payload)
