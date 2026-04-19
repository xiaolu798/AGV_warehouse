import request from './request'

export const fetchMissions = () => request.get('/mission/')

export const createMissionApi = (payload) => request.post('/mission/', payload)

export const assignMissionApi = (missionId, deviceCode) =>
  request.post('/mission/assign', {
    mission_id: missionId,
    device_code: deviceCode,
  })

export const cancelMissionApi = (missionId, deviceCode = null) =>
  request.post('/mission/cancel', {
    mission_id: missionId,
    device_code: deviceCode,
  })

export const finishMissionApi = (missionId, deviceCode = null) =>
  request.post('/mission/finish', {
    mission_id: missionId,
    device_code: deviceCode,
  })
