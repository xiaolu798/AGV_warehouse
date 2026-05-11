import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDevices, updateDeviceStatusApi, deleteDeviceApi } from '../api/device'

const HEARTBEAT_INTERVAL = 20000
const HEARTBEAT_TIMEOUT = 45000
const RECONNECT_BASE_DELAY = 3000
const RECONNECT_MAX_DELAY = 15000

const statusTextMap = {
  0: '空闲',
  1: '忙碌',
  2: '故障',
}

const taskTextMap = {
  0: '待执行',
  1: '进行中',
  2: '已完成',
  3: '异常',
  '-1': '已取消',
}

const nowString = () => {
  const d = new Date()
  return d.toTimeString().slice(0, 8)
}

export const useDeviceStore = defineStore('device', () => {
  const devices = ref([])
  const runtimeLogs = ref([])
  const wsConnected = ref(false)
  const deviceLoading = ref(false)

  const ws = ref(null)
  const heartbeatTimer = ref(null)
  const reconnectTimer = ref(null)
  const reconnectAttempts = ref(0)
  const lastPongAt = ref(Date.now())
  const manualClose = ref(false)
  const wsSubscribers = new Set()

  const totalCount = computed(() => devices.value.length)
  const runningCount = computed(() => devices.value.filter((d) => d.work_status === 1).length)
  const faultCount = computed(() => devices.value.filter((d) => d.work_status === 2).length)

  const sortedDevices = computed(() =>
    [...devices.value].sort((a, b) => a.device_code.localeCompare(b.device_code)),
  )

  const upsertDevice = (payload) => {
    const target = devices.value.find((d) => d.device_code === payload.device_code)
    if (target) {
      Object.assign(target, payload)
      return target
    }
    devices.value.push({
      ...payload,
      task_status: payload.task_status ?? 0,
      flashUntil: Date.now() + 1200,
      ip_addr: payload.ip_addr || '--',
      firmware: payload.firmware || '--',
      mileage: payload.mileage || 0,
    })
    return devices.value[devices.value.length - 1]
  }

  const appendLog = (text) => {
    runtimeLogs.value.unshift(`[${nowString()}] ${text}`)
    runtimeLogs.value = runtimeLogs.value.slice(0, 80)
  }

  const notifySubscribers = (message) => {
    wsSubscribers.forEach((handler) => {
      try {
        handler(message)
      } catch (error) {
        console.error('WebSocket subscriber error:', error)
      }
    })
  }

  const normalizeDevices = (rows = []) => {
    return rows
      .filter((item) => item && item.device_code)
      .map((item) => ({
        ...item,
        task_status: item.task_status ?? 0,
        flashUntil: 0,
        ip_addr: item.ip_addr || '--',
        firmware: item.firmware || '--',
        mileage: item.mileage || 0,
      }))
      .sort((a, b) => a.device_code.localeCompare(b.device_code))
  }

  const applyStatusUpdate = (data = {}) => {
    if (!data.device_code) return
    const target = upsertDevice({
      device_code: data.device_code,
      work_status: data.work_status ?? 0,
      task_status: data.task_status ?? 0,
      battery: data.battery ?? 100,
      flashUntil: Date.now() + 1500,
    })
    appendLog(
      `${target.device_code} 状态更新 -> 设备:${statusTextMap[target.work_status] || '未知'} 任务:${
        taskTextMap[target.task_status] || '未知'
      }`,
    )
  }

  const applyMissionCompleted = (data = {}) => {
    if (data.device) {
      const target = upsertDevice({
        device_code: data.device,
        work_status: 0,
        flashUntil: Date.now() + 1500,
      })
      appendLog(`${target.device_code} 已完成任务，设备恢复空闲`)
    }
    if (data.from || data.to) {
      appendLog(`任务完成 -> ${data.from || '--'} -> ${data.to || '--'}`)
    }
  }

  const wsUrl = () => {
    if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    return `${protocol}://${window.location.host}/ws/devices`
  }

  const cleanupWsTimers = () => {
    if (heartbeatTimer.value) clearInterval(heartbeatTimer.value)
    heartbeatTimer.value = null
    if (reconnectTimer.value) clearTimeout(reconnectTimer.value)
    reconnectTimer.value = null
  }

  const startHeartbeat = () => {
    cleanupWsTimers()
    heartbeatTimer.value = setInterval(() => {
      const stale = Date.now() - lastPongAt.value > HEARTBEAT_TIMEOUT
      if (stale) {
        appendLog('心跳超时，尝试重连')
        ws.value?.close()
        return
      }
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send('ping')
      }
    }, HEARTBEAT_INTERVAL)
  }

  const scheduleReconnect = () => {
    cleanupWsTimers()
    wsConnected.value = false
    reconnectAttempts.value += 1
    const delay = Math.min(RECONNECT_BASE_DELAY * reconnectAttempts.value, RECONNECT_MAX_DELAY)
    reconnectTimer.value = setTimeout(() => {
      connectWs()
    }, delay)
  }

  const connectWs = () => {
    if (ws.value && [WebSocket.OPEN, WebSocket.CONNECTING].includes(ws.value.readyState)) return
    manualClose.value = false
    const socket = new WebSocket(wsUrl())
    ws.value = socket
    socket.onopen = () => {
      wsConnected.value = true
      reconnectAttempts.value = 0
      lastPongAt.value = Date.now()
      appendLog('WebSocket 已连接')
      startHeartbeat()
    }
    socket.onmessage = (evt) => {
      if (evt.data === 'pong') {
        lastPongAt.value = Date.now()
        return
      }
      try {
        const message = JSON.parse(evt.data)
        if (message.event === 'update_status') {
          applyStatusUpdate(message.data)
        } else if (message.event === 'mission_completed') {
          applyMissionCompleted(message.data)
        }
        notifySubscribers(message)
      } catch (error) {
        appendLog(`收到非 JSON 消息: ${String(evt.data).slice(0, 60)}`)
      }
    }
    socket.onclose = () => {
      wsConnected.value = false
      appendLog('WebSocket 已断开')
      if (ws.value === socket) ws.value = null
      if (manualClose.value) return
      scheduleReconnect()
    }
    socket.onerror = () => {
      wsConnected.value = false
      appendLog('WebSocket 连接异常')
    }
  }

  const disconnectWs = () => {
    manualClose.value = true
    cleanupWsTimers()
    if (ws.value && [WebSocket.OPEN, WebSocket.CONNECTING].includes(ws.value.readyState)) {
      ws.value.close()
    }
    ws.value = null
    wsConnected.value = false
  }

  const loadDevices = async () => {
    deviceLoading.value = true
    try {
      const rows = await fetchDevices()
      devices.value = normalizeDevices(Array.isArray(rows) ? rows : [])
      appendLog(`设备列表已同步，共 ${devices.value.length} 台`)
    } finally {
      deviceLoading.value = false
    }
  }

  const setDeviceStatus = async (row, status) => {
    await updateDeviceStatusApi(row.id, status)
    upsertDevice({
      ...row,
      work_status: status,
      flashUntil: Date.now() + 800,
    })
    appendLog(`${row.device_code} 手动切换为 ${statusTextMap[status] || status}`)
  }

  const resetDevice = async (row) => setDeviceStatus(row, 0)

  const removeDevice = async (row) => {
    await deleteDeviceApi(row.id)
    devices.value = devices.value.filter((d) => d.id !== row.id)
    appendLog(`${row.device_code} 已停用/删除`)
  }

  const initRealtime = async () => {
    await loadDevices()
    connectWs()
  }

  const subscribeWsMessages = (handler) => {
    wsSubscribers.add(handler)
    return () => {
      wsSubscribers.delete(handler)
    }
  }

  return {
    devices,
    sortedDevices,
    runtimeLogs,
    wsConnected,
    deviceLoading,
    totalCount,
    runningCount,
    faultCount,
    loadDevices,
    connectWs,
    disconnectWs,
    initRealtime,
    applyStatusUpdate,
    appendLog,
    subscribeWsMessages,
    setDeviceStatus,
    resetDevice,
    removeDevice,
  }
})
