import request from './request'

export const fetchDevices = () => request.get('/devices/')

export const updateDeviceStatusApi = (deviceId, status) =>
  request.post('/devices/status', null, {
    params: { device_id: deviceId, status },
  })

export const deleteDeviceApi = (deviceId) => request.delete(`/devices/${deviceId}`)
