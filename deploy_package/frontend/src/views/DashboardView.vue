<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDeviceStore } from '../stores/device'
import {
  assignMissionApi,
  cancelMissionApi,
  createMissionApi,
  fetchMissions,
} from '../api/mission'
import { createWarehouseApi, fetchWarehouseMatrix, fetchWarehouses } from '../api/warehouse'

const deviceStore = useDeviceStore()

const taskStatusTextMap = {
  '-1': '已取消',
  0: '待处理',
  1: '执行中',
  2: '已完成',
  3: '异常',
}

const taskStatusTagMap = {
  '-1': 'bg-slate-200 text-slate-600',
  0: 'bg-slate-200 text-slate-700',
  1: 'bg-blue-100 text-blue-700',
  2: 'bg-emerald-100 text-emerald-700',
  3: 'bg-rose-100 text-rose-700',
}

const deviceStatusTextMap = {
  0: '空闲',
  1: '作业中',
  2: '故障',
}

const warehouses = ref([])
const selectedWarehouseId = ref(null)
const warehouseInfo = ref(null)
const matrixCells = ref([])
const missions = ref([])
const deviceStatusFilter = ref('all')
const deviceKeyword = ref('')
const focusedLocationCode = ref('')

const warehouseLoading = ref(false)
const matrixLoading = ref(false)
const missionLoading = ref(false)
const creatingMission = ref(false)
const warehouseDialogVisible = ref(false)
const warehouseSubmitting = ref(false)

const selection = reactive({
  start: null,
  end: null,
})

const warehouseForm = reactive({
  name: '',
  code: '',
  rows: 8,
  cols: 10,
  description: '',
})

const debugForm = reactive({
  missionId: null,
  deviceCode: null,
})

let unsubscribeWs = null

const statCards = computed(() => [
  {
    title: '仓库数量',
    value: warehouses.value.length,
    panel: 'from-[#6557e6] to-[#8b7cf8]',
  },
  {
    title: '待执行任务',
    value: missions.value.filter((item) => item.status === 0).length,
    panel: 'from-[#5b86ff] to-[#6d7cff]',
  },
  {
    title: '执行中任务',
    value: missions.value.filter((item) => item.status === 1).length,
    panel: 'from-[#ff8da1] to-[#ff7a59]',
  },
  {
    title: '在线设备',
    value: deviceStore.totalCount,
    panel: 'from-[#56c1b2] to-[#40a7c7]',
  },
])

const currentWarehouse = computed(() =>
  warehouses.value.find((item) => item.id === selectedWarehouseId.value) || null,
)

const matrixStyle = computed(() => {
  const cols = Math.max(warehouseInfo.value?.cols || 1, 1)
  return {
    gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
  }
})

const debugMissionOptions = computed(() =>
  missions.value
    .filter((item) => item.status === 0)
    .map((item) => ({
      label: `${item.mission_no} · ${missionPath(item)}`,
      value: item.id,
    })),
)

const deviceStatusCards = computed(() => [
  {
    key: 'all',
    label: '全部',
    count: deviceStore.devices.length,
    activeClass: 'border-slate-900 bg-slate-900 text-white',
  },
  {
    key: 0,
    label: '空闲',
    count: deviceStore.devices.filter((item) => item.work_status === 0).length,
    activeClass: 'border-emerald-500 bg-emerald-500 text-white',
  },
  {
    key: 1,
    label: '作业中',
    count: deviceStore.devices.filter((item) => item.work_status === 1).length,
    activeClass: 'border-blue-500 bg-blue-500 text-white',
  },
  {
    key: 2,
    label: '故障',
    count: deviceStore.devices.filter((item) => item.work_status === 2).length,
    activeClass: 'border-rose-500 bg-rose-500 text-white',
  },
])

const sortedFilteredDevices = computed(() => {
  const keyword = deviceKeyword.value.trim().toLowerCase()
  const statusRankMap = {
    2: 0,
    0: 1,
    1: 2,
  }

  return [...deviceStore.devices]
    .filter((item) => {
      const matchesStatus =
        deviceStatusFilter.value === 'all' || item.work_status === deviceStatusFilter.value
      const matchesKeyword =
        !keyword || item.device_code?.toLowerCase().includes(keyword)
      return matchesStatus && matchesKeyword
    })
    .sort((a, b) => {
      const statusDiff = (statusRankMap[a.work_status] ?? 99) - (statusRankMap[b.work_status] ?? 99)
      if (statusDiff !== 0) return statusDiff
      const batteryDiff = (b.battery ?? 0) - (a.battery ?? 0)
      if (batteryDiff !== 0) return batteryDiff
      return (a.device_code || '').localeCompare(b.device_code || '')
    })
})

const assignableDeviceOptions = computed(() =>
  [...deviceStore.devices]
    .filter((item) => item.work_status === 0 && Number(item.battery ?? 0) > 20)
    .sort((a, b) => (b.battery ?? 0) - (a.battery ?? 0) || a.device_code.localeCompare(b.device_code))
    .map((item) => {
      const focusPayload = resolveDeviceFocusPayload(item)
      return {
        value: item.device_code,
        label: `${item.device_code} | ${item.battery ?? '--'}% | ${focusPayload.location_code || '未知位置'}`,
      }
    }),
)

const formatTime = (value) => (value ? new Date(value).toLocaleString() : '--')

const missionPath = (row) =>
  `${row.from_location?.location_code || '--'} -> ${row.to_location?.location_code || '--'}`

const warehouseUsageText = (row) => {
  const total = row?.total_slots || 0
  const used = row?.used_slots || 0
  if (!total) return '0%'
  return `${Math.round((used / total) * 100)}%`
}

const clearSelection = () => {
  selection.start = null
  selection.end = null
}

const updateMatrixCellStatus = (code, status) => {
  if (!code) return
  const target = matrixCells.value.find((item) => item.code === code)
  if (target) target.status = status
}

const currentMissionByDevice = (deviceCode) =>
  missions.value.find(
    (item) =>
      item.device?.device_code === deviceCode && item.status !== 2 && item.status !== -1,
  ) || null

const resolveDeviceFocusPayload = (device) => {
  const currentMission = currentMissionByDevice(device.device_code)
  const locationCode =
    currentMission?.to_location?.location_code ||
    currentMission?.from_location?.location_code ||
    device.location_code ||
    ''
  const matrixCell = matrixCells.value.find((item) => item.code === locationCode)

  return {
    device_code: device.device_code,
    location_code: locationCode || '',
    row: matrixCell?.r ?? null,
    col: matrixCell?.c ?? null,
    mission_id: currentMission?.id ?? null,
  }
}

const locateDeviceOnMatrix = (device) => {
  const payload = resolveDeviceFocusPayload(device)
  focusedLocationCode.value = payload.location_code || ''
  window.dispatchEvent(
    new CustomEvent('agv-device-focus', {
      detail: payload,
    }),
  )
  if (payload.location_code) {
    deviceStore.appendLog(`定位设备 ${payload.device_code} -> ${payload.location_code}`)
  } else {
    deviceStore.appendLog(`设备 ${payload.device_code} 暂无可定位库位`)
  }
}

const syncMissionRow = (data = {}) => {
  const target = missions.value.find((item) => item.id === data.mission_id)
  if (!target) return
  if (typeof data.task_status === 'number') target.status = data.task_status
  if (data.device_code) {
    target.device = {
      ...(target.device || {}),
      device_code: data.device_code,
    }
  }
  if (data.from_location) {
    target.from_location = {
      ...(target.from_location || {}),
      location_code: data.from_location,
    }
  }
  if (data.to_location) {
    target.to_location = {
      ...(target.to_location || {}),
      location_code: data.to_location,
    }
  }
}

const applyMissionToMatrix = (mission, status) => {
  const fromCode = mission?.from_location?.location_code
  const toCode = mission?.to_location?.location_code
  if (status === 1) {
    updateMatrixCellStatus(fromCode, 2)
    updateMatrixCellStatus(toCode, 2)
  }
  if (status === 2) {
    updateMatrixCellStatus(fromCode, 0)
    updateMatrixCellStatus(toCode, 1)
  }
  if (status === -1) {
    updateMatrixCellStatus(fromCode, 1)
    updateMatrixCellStatus(toCode, 0)
  }
}

const handleWsMessage = (message = {}) => {
  if (message.event === 'update_status') {
    const payload = message.data || {}
    syncMissionRow(payload)
    const target = missions.value.find((item) => item.id === payload.mission_id)
    if ((payload.task_status === 1 || payload.task_status === 2) && target) {
      applyMissionToMatrix(target, payload.task_status)
    }
    return
  }

  if (message.event === 'mission_completed') {
    const payload = message.data || {}
    const target = missions.value.find((item) => item.hardware_id === payload.h_id)
    if (target) {
      target.status = 2
      if (payload.device) {
        target.device = {
          ...(target.device || {}),
          device_code: payload.device,
        }
      }
    }
    updateMatrixCellStatus(payload.from, 0)
    updateMatrixCellStatus(payload.to, 1)
  }
}

const loadWarehouses = async (preferredCode = null) => {
  warehouseLoading.value = true
  try {
    const rows = await fetchWarehouses()
    warehouses.value = Array.isArray(rows) ? rows : []

    if (preferredCode) {
      const next = warehouses.value.find((item) => item.code === preferredCode)
      if (next) {
        selectedWarehouseId.value = next.id
        return
      }
    }

    if (!warehouses.value.length) {
      selectedWarehouseId.value = null
      warehouseInfo.value = null
      matrixCells.value = []
      return
    }

    const exists = warehouses.value.some((item) => item.id === selectedWarehouseId.value)
    if (!exists) {
      selectedWarehouseId.value = warehouses.value[0].id
    }
  } finally {
    warehouseLoading.value = false
  }
}

const loadMatrix = async (warehouseId) => {
  if (!warehouseId) return
  matrixLoading.value = true
  try {
    const data = await fetchWarehouseMatrix(warehouseId)
    warehouseInfo.value = data?.info || null
    matrixCells.value = Array.isArray(data?.matrix)
      ? [...data.matrix].sort((a, b) => a.r - b.r || a.c - b.c)
      : []
  } finally {
    matrixLoading.value = false
  }
}

const loadMissions = async () => {
  missionLoading.value = true
  try {
    const rows = await fetchMissions()
    missions.value = Array.isArray(rows) ? rows : []
  } finally {
    missionLoading.value = false
  }
}

const openWarehouseDialog = () => {
  warehouseForm.name = ''
  warehouseForm.code = ''
  warehouseForm.rows = 8
  warehouseForm.cols = 10
  warehouseForm.description = ''
  warehouseDialogVisible.value = true
}

const submitWarehouse = async () => {
  warehouseSubmitting.value = true
  try {
    await createWarehouseApi({
      name: warehouseForm.name,
      code: warehouseForm.code,
      rows: Number(warehouseForm.rows),
      cols: Number(warehouseForm.cols),
      description: warehouseForm.description,
    })
    ElMessage.success('仓库创建成功')
    warehouseDialogVisible.value = false
    await loadWarehouses(warehouseForm.code)
  } finally {
    warehouseSubmitting.value = false
  }
}

const createMission = async () => {
  if (!selection.start || !selection.end) return
  creatingMission.value = true
  try {
    const data = await createMissionApi({
      type: 3,
      priority: 0,
      from_location: selection.start,
      to_location: selection.end,
    })
    updateMatrixCellStatus(selection.start, 2)
    updateMatrixCellStatus(selection.end, 2)
    deviceStore.appendLog(`创建任务 ${data?.mission_no || ''} ${selection.start} -> ${selection.end}`)
    ElMessage.success(`任务已创建 ${data?.mission_no || ''}`)
    clearSelection()
    await loadMissions()
    await loadWarehouses(currentWarehouse.value?.code || null)
  } finally {
    creatingMission.value = false
  }
}

const handleCellClick = async (cell) => {
  if (cell.status === 2) {
    ElMessage.warning('锁定中的库位暂不可操作')
    return
  }

  if (selection.start === cell.code) {
    selection.start = null
    selection.end = null
    return
  }

  if (selection.end === cell.code) {
    selection.end = null
    return
  }

  if (!selection.start) {
    if (cell.status !== 1) {
      ElMessage.info('请先选择一个占用中的蓝色库位作为起点')
      return
    }
    selection.start = cell.code
    selection.end = null
    return
  }

  if (cell.status === 1) {
    selection.start = cell.code
    selection.end = null
    return
  }

  if (cell.status !== 0) {
    ElMessage.info('终点必须是空闲库位')
    return
  }

  selection.end = cell.code

  try {
    await ElMessageBox.confirm(
      `确认创建搬运任务？\n起点：${selection.start}\n终点：${selection.end}`,
      '创建任务',
      {
        type: 'warning',
        confirmButtonText: '确认创建',
        cancelButtonText: '取消',
      },
    )
    await createMission()
  } catch {
    selection.end = null
  }
}

const cancelMission = async (row) => {
  await cancelMissionApi(row.id, row.device?.device_code || null)
  row.status = -1
  applyMissionToMatrix(row, -1)
  deviceStore.appendLog(`任务 ${row.mission_no} 已撤销`)
  ElMessage.success(`任务 ${row.mission_no} 已撤销`)
}

const runAssignDebug = async () => {
  if (!debugForm.missionId || !debugForm.deviceCode) {
    ElMessage.warning('请选择待处理任务和设备')
    return
  }
  await assignMissionApi(debugForm.missionId, debugForm.deviceCode)
  const target = missions.value.find((item) => item.id === debugForm.missionId)
  if (target) {
    target.status = 1
    target.device = {
      ...(target.device || {}),
      device_code: debugForm.deviceCode,
    }
    applyMissionToMatrix(target, 1)
    deviceStore.appendLog(`手动指派 ${target.mission_no} -> ${debugForm.deviceCode}`)
  }
  debugForm.missionId = null
  debugForm.deviceCode = null
  ElMessage.success('设备已手动指派，任务进入执行中')
}

const cellClass = (cell) => {
  if (selection.start === cell.code) {
    return 'border-[#4f46e5] bg-[#dfe3ff] ring-2 ring-[#4f46e5]'
  }
  if (selection.end === cell.code) {
    return 'border-[#14b8a6] bg-[#dcfdf7] ring-2 ring-[#14b8a6]'
  }
  if (focusedLocationCode.value === cell.code) {
    return 'border-[#f59e0b] bg-[#fff6db] text-[#92400e] ring-2 ring-[#f59e0b]'
  }
  if (cell.status === 2) {
    return 'border-[#ff8a4c] bg-[#fff0e2] text-[#9a3412] animate-pulse'
  }
  if (cell.status === 1) {
    return 'border-[#7ea4ff] bg-[#edf3ff] text-[#3156be]'
  }
  return 'border-slate-200 bg-[#f4f5fb] text-slate-500'
}

const batteryClass = (value = 0) => {
  if (value < 10) return 'bg-rose-500 animate-pulse'
  if (value <= 30) return 'bg-amber-400'
  return 'bg-emerald-500'
}

watch(
  selectedWarehouseId,
  async (id) => {
    clearSelection()
    if (id) {
      await loadMatrix(id)
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (!deviceStore.devices.length) {
    await deviceStore.loadDevices()
  }
  await Promise.all([loadWarehouses(), loadMissions()])
  unsubscribeWs = deviceStore.subscribeWsMessages(handleWsMessage)
})

onBeforeUnmount(() => {
  if (unsubscribeWs) unsubscribeWs()
})
</script>

<template>
  <section class="space-y-6">
    <header class="overflow-hidden rounded-[32px] bg-gradient-to-br from-[#6254e7] via-[#7368ee] to-[#ff8fb1] p-6 text-white shadow-panel">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.32em] text-white/70">Primary Dashboard</p>
          <h2 class="mt-2 text-3xl font-extrabold">仓库数字孪生与 AGV 任务联动大屏</h2>
          <p class="mt-3 max-w-3xl text-sm text-white/85">
            左侧基于 `/warehouse` 与 `/matrix` 构建仓库矩阵，右侧联动任务、设备与 WebSocket 状态。
          </p>
        </div>
        <div class="rounded-full bg-white/20 px-4 py-2 text-sm text-white/90">
          {{ deviceStore.wsConnected ? 'WebSocket 已连接' : 'WebSocket 连接中' }}
        </div>
      </div>
      <div class="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div
          v-for="item in statCards"
          :key="item.title"
          class="rounded-[24px] bg-gradient-to-br p-5 shadow-[0_18px_34px_rgba(43,32,120,0.18)]"
          :class="item.panel"
        >
          <p class="text-xs tracking-[0.25em] text-white/75">{{ item.title }}</p>
          <p class="mt-3 text-4xl font-extrabold text-white">{{ item.value }}</p>
        </div>
      </div>
    </header>

    <section class="rounded-[28px] bg-white p-5 shadow-panel">
      <div class="mb-4 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-slate-800">实时日志流</h3>
        <span class="text-xs text-slate-400">最近 80 条</span>
      </div>
      <div class="h-[260px] space-y-2 overflow-auto rounded-[24px] bg-[#1f2854] p-4 pr-2 text-xs leading-5 text-slate-200">
        <p v-for="(line, index) in deviceStore.runtimeLogs" :key="`${line}-${index}`" class="font-mono">
          {{ line }}
        </p>
      </div>
    </section>

    <div class="grid grid-cols-12 gap-6">
      <div class="col-span-12 space-y-6 xl:col-span-8">
        <section class="rounded-[28px] bg-white p-5 shadow-panel">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <h3 class="text-lg font-semibold text-slate-800">仓库管理</h3>
              <p class="mt-1 text-sm text-slate-500">显示仓库列表、库位总数和占用比例，可直接创建新仓库。</p>
            </div>
            <el-button type="primary" @click="openWarehouseDialog">新建仓库</el-button>
          </div>

          <div
            v-if="warehouseLoading"
            class="mt-5 flex h-36 items-center justify-center rounded-[24px] bg-slate-50 text-slate-400"
          >
            正在加载仓库列表...
          </div>

          <div v-else-if="!warehouses.length" class="mt-5 rounded-[24px] bg-slate-50 p-8 text-center text-slate-400">
            当前没有仓库，请先创建仓库
          </div>

          <div v-else class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 2xl:grid-cols-3">
            <button
              v-for="item in warehouses"
              :key="item.id"
              class="rounded-[24px] border p-5 text-left transition-all"
              :class="
                selectedWarehouseId === item.id
                  ? 'border-[#6d63ec] bg-[#f1efff] shadow-[0_18px_34px_rgba(109,99,236,0.14)]'
                  : 'border-slate-200 bg-[#fbfbff] hover:border-[#c7c4ff]'
              "
              @click="selectedWarehouseId = item.id"
            >
              <div class="flex items-start justify-between">
                <div>
                  <p class="text-lg font-bold text-slate-800">{{ item.name }}</p>
                  <p class="mt-1 text-sm text-slate-500">{{ item.code }}</p>
                </div>
                <span class="rounded-full bg-white px-3 py-1 text-xs text-slate-500">
                  {{ item.rows }} x {{ item.cols }}
                </span>
              </div>
              <div class="mt-5 grid grid-cols-2 gap-3">
                <div class="rounded-2xl bg-white p-3">
                  <p class="text-xs text-slate-400">总库位</p>
                  <p class="mt-1 text-xl font-bold text-slate-800">{{ item.total_slots || 0 }}</p>
                </div>
                <div class="rounded-2xl bg-white p-3">
                  <p class="text-xs text-slate-400">占用比例</p>
                  <p class="mt-1 text-xl font-bold text-slate-800">{{ warehouseUsageText(item) }}</p>
                </div>
              </div>
            </button>
          </div>
        </section>

        <section class="rounded-[28px] bg-white p-5 shadow-panel">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <h3 class="text-lg font-semibold text-slate-800">数字孪生矩阵</h3>
              <p class="mt-1 text-sm text-slate-500">
                先点蓝色库位作为起点，再点灰色库位作为终点，确认后自动调用 `/mission/` 创建任务。
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-xs">
              <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">空闲: 灰色</span>
              <span class="rounded-full bg-blue-100 px-3 py-1 text-blue-700">占用: 蓝色</span>
              <span class="rounded-full bg-orange-100 px-3 py-1 text-orange-700">锁定: 橙色</span>
            </div>
          </div>

          <div class="mt-5 flex flex-wrap gap-3 text-sm text-slate-500">
            <span class="rounded-full bg-[#eff1fb] px-4 py-2">
              当前仓库：{{ currentWarehouse?.name || '未选择' }}
            </span>
            <span class="rounded-full bg-[#eff1fb] px-4 py-2">起点：{{ selection.start || '--' }}</span>
            <span class="rounded-full bg-[#eff1fb] px-4 py-2">终点：{{ selection.end || '--' }}</span>
          </div>

          <div
            v-if="matrixLoading"
            class="mt-5 flex h-[520px] items-center justify-center rounded-[24px] bg-[#f6f7fc] text-slate-400"
          >
            正在加载仓库矩阵...
          </div>

          <div
            v-else-if="!matrixCells.length"
            class="mt-5 flex h-[520px] items-center justify-center rounded-[24px] bg-[#f6f7fc] text-slate-400"
          >
            当前仓库暂无矩阵数据
          </div>

          <div v-else class="mt-5 rounded-[28px] bg-[#f5f7ff] p-4">
            <div class="grid gap-2" :style="matrixStyle">
              <button
                v-for="cell in matrixCells"
                :key="cell.id"
                class="relative min-h-[64px] rounded-[18px] border p-2 text-left transition-all"
                :class="cellClass(cell)"
                @click="handleCellClick(cell)"
              >
                <span class="block text-[11px] font-medium text-slate-400">R{{ cell.r }} C{{ cell.c }}</span>
                <span class="mt-1 block text-sm font-bold">{{ cell.code }}</span>
                <span
                  v-if="selection.start === cell.code"
                  class="absolute right-2 top-2 rounded-full bg-[#4f46e5] px-2 py-0.5 text-[10px] font-bold text-white"
                >
                  起点
                </span>
                <span
                  v-else-if="selection.end === cell.code"
                  class="absolute right-2 top-2 rounded-full bg-[#14b8a6] px-2 py-0.5 text-[10px] font-bold text-white"
                >
                  终点
                </span>
              </button>
            </div>
          </div>
        </section>
      </div>

      <aside class="col-span-12 space-y-6 xl:col-span-4">
        <section class="rounded-[28px] bg-white p-5 shadow-panel">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-slate-800">任务与调试面板</h3>
              <p class="mt-1 text-sm text-slate-500">支持任务撤销与手动指派，完成状态等待后端 TCP 自动闭环。</p>
            </div>
            <el-button type="primary" plain @click="loadMissions">刷新</el-button>
          </div>

          <div class="mt-5 rounded-[24px] bg-[#f7f8ff] p-4">
            <p class="text-sm font-semibold text-slate-700">调试控制台</p>
            <div class="mt-3 space-y-3">
              <el-select v-model="debugForm.missionId" placeholder="选择待指派任务" class="w-full" clearable>
                <el-option
                  v-for="item in debugMissionOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <el-select
                v-model="debugForm.deviceCode"
                placeholder="搜索并选择空闲设备"
                class="w-full"
                clearable
                filterable
              >
                <el-option
                  v-for="item in assignableDeviceOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <p class="text-xs text-slate-400">
                仅显示空闲且电量大于 20% 的设备，任务领取后转为执行中，只读等待后端回传完成。
              </p>
              <el-button type="primary" class="w-full" :disabled="!debugMissionOptions.length" @click="runAssignDebug">
                手动指派
              </el-button>
            </div>
          </div>

          <div v-if="missionLoading" class="mt-5 text-sm text-slate-400">正在加载任务...</div>

          <div v-else class="mt-5 max-h-[420px] space-y-3 overflow-auto pr-1">
            <div
              v-for="row in missions"
              :key="row.id"
              class="rounded-[22px] border border-slate-200 bg-[#fcfcff] p-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-semibold text-slate-800">{{ row.mission_no }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ missionPath(row) }}</p>
                </div>
                <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="taskStatusTagMap[row.status]">
                  {{ taskStatusTextMap[row.status] || '未知' }}
                </span>
              </div>
              <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div class="rounded-2xl bg-white p-3">
                  <p class="text-xs text-slate-400">设备</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ row.device?.device_code || '--' }}</p>
                </div>
                <div class="rounded-2xl bg-white p-3">
                  <p class="text-xs text-slate-400">硬件号</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ row.hardware_id || '--' }}</p>
                </div>
              </div>
              <p class="mt-3 text-xs text-slate-400">{{ formatTime(row.create_time) }}</p>
              <div class="mt-3 flex items-center justify-end gap-3">
                <el-button v-if="row.status === 0" type="danger" link @click="cancelMission(row)">
                  撤销任务
                </el-button>
                <span v-else-if="row.status === 1" class="text-xs text-slate-400">已指派，等待设备/TCP 回传完成</span>
                <span v-else class="text-xs text-slate-400">等待 WebSocket 联动更新</span>
              </div>
            </div>
            <div v-if="!missions.length" class="rounded-[22px] bg-slate-50 p-6 text-center text-sm text-slate-400">
              当前没有任务数据
            </div>
          </div>
        </section>

        <section class="rounded-[28px] bg-white p-5 shadow-panel">
          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-slate-800">设备监控</h3>
                <p class="mt-1 text-sm text-slate-500">支持状态过滤、模糊搜索、优先级排序与地图定位。</p>
              </div>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">
                共 {{ deviceStore.totalCount }} 台
              </span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="item in deviceStatusCards"
                :key="item.key"
                class="rounded-2xl border px-3 py-3 text-left transition-all"
                :class="
                  deviceStatusFilter === item.key
                    ? item.activeClass
                    : 'border-slate-200 bg-[#f8f9ff] text-slate-600 hover:border-slate-300'
                "
                @click="deviceStatusFilter = item.key"
              >
                <p class="text-xs opacity-80">{{ item.label }}</p>
                <p class="mt-1 text-xl font-bold">{{ item.count }}</p>
              </button>
            </div>
            <el-input
              v-model="deviceKeyword"
              clearable
              placeholder="搜索设备编号，例如 AGV-001"
            />
          </div>

          <div v-if="deviceStore.deviceLoading" class="mt-5 text-sm text-slate-400">设备加载中...</div>

          <div v-else class="mt-5 max-h-[640px] space-y-3 overflow-auto pr-1">
            <div
              v-for="device in sortedFilteredDevices"
              :key="device.device_code"
              class="cursor-pointer rounded-[22px] border border-slate-200 bg-[#fcfcff] p-4 transition-all hover:border-[#8c84ff] hover:shadow-[0_18px_34px_rgba(109,99,236,0.12)]"
              @click="locateDeviceOnMatrix(device)"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-semibold text-slate-800">{{ device.device_code }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ deviceStatusTextMap[device.work_status] || '未知' }}</p>
                </div>
                <span
                  class="rounded-full px-3 py-1 text-xs font-semibold"
                  :class="
                    device.work_status === 2
                      ? 'bg-rose-100 text-rose-600'
                      : device.work_status === 1
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-emerald-100 text-emerald-600'
                  "
                >
                  {{ deviceStatusTextMap[device.work_status] || '未知' }}
                </span>
              </div>
              <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div class="rounded-2xl bg-white p-3">
                  <p class="text-xs text-slate-400">当前位置</p>
                  <p class="mt-1 font-semibold text-slate-700">{{ resolveDeviceFocusPayload(device).location_code || '--' }}</p>
                </div>
                <div class="rounded-2xl bg-white p-3">
                  <p class="text-xs text-slate-400">定位坐标</p>
                  <p class="mt-1 font-semibold text-slate-700">
                    {{
                      resolveDeviceFocusPayload(device).row !== null
                        ? `R${resolveDeviceFocusPayload(device).row} C${resolveDeviceFocusPayload(device).col}`
                        : '--'
                    }}
                  </p>
                </div>
              </div>
              <div class="mt-4">
                <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
                  <span>电量</span>
                  <span>{{ device.battery ?? '--' }}%</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    class="h-full rounded-full transition-all"
                    :class="batteryClass(device.battery)"
                    :style="{ width: `${Math.max(0, Math.min(device.battery ?? 0, 100))}%` }"
                  ></div>
                </div>
              </div>
              <p class="mt-3 text-xs text-slate-400">点击卡片可派发设备定位事件并高亮当前矩阵库位</p>
            </div>
            <div
              v-if="!sortedFilteredDevices.length"
              class="rounded-[22px] bg-slate-50 p-6 text-center text-sm text-slate-400"
            >
              当前筛选条件下没有设备数据
            </div>
          </div>
        </section>

      </aside>
    </div>

    <el-dialog v-model="warehouseDialogVisible" title="新建仓库" width="520px">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <el-input v-model="warehouseForm.name" placeholder="仓库名称" />
        <el-input v-model="warehouseForm.code" placeholder="仓库编码，如 WH-A" />
        <el-input-number v-model="warehouseForm.rows" :min="1" :max="100" class="!w-full" />
        <el-input-number v-model="warehouseForm.cols" :min="1" :max="100" class="!w-full" />
        <el-input
          v-model="warehouseForm.description"
          type="textarea"
          :rows="3"
          placeholder="仓库描述"
          class="md:col-span-2"
        />
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="warehouseDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="warehouseSubmitting" @click="submitWarehouse">
            创建仓库
          </el-button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>
