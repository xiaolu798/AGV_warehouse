import request from './request'

export const fetchWarehouses = () => request.get('/warehouse')

export const createWarehouseApi = (payload) => request.post('/warehouse', payload)

export const fetchWarehouseMatrix = (warehouseId) => request.get(`/warehouse/${warehouseId}/matrix`)
