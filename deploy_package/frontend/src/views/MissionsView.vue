<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { cancelMissionApi, fetchMissions } from '../api/mission'
import { useDeviceStore } from '../stores/device'

const deviceStore = useDeviceStore()
const loading = ref(false)
const missions = ref([])
let unsubscribeWs = null

const filters = reactive({
  missionNo: '',
  deviceCode: '',
  dateRange: [],
})

const statusTypeMap = {
  '-1': 'info',
  0: 'info',
  1: 'primary',
  2: 'success',
  3: 'danger',
}

const statusTextMap = {
  '-1': '已取消',
  0: '待处理',
  1: '执行中',
  2: '已完成',
  3: '异常',
}

const formatTime = (v) => (v ? new Date(v).toLocaleString() : '--')

const missionPath = (row) =>
  `${row.from_location?.location_code || '--'} -> ${row.to_location?.location_code || '--'}`

const loadMissions = async () => {
  loading.value = true
  try {
    const rows = await fetchMissions()
    missions.value = Array.isArray(rows) ? rows : []
  } finally {
    loading.value = false
  }
}

const filteredMissions = computed(() => {
  return missions.value.filter((row) => {
    const missionNoOk = !filters.missionNo || row.mission_no?.includes(filters.missionNo.trim())
    const deviceCode = row.device?.device_code || ''
    const deviceOk = !filters.deviceCode || deviceCode.includes(filters.deviceCode.trim())
    const dateOk =
      !filters.dateRange?.length ||
      (new Date(row.create_time) >= new Date(filters.dateRange[0]) &&
        new Date(row.create_time) <= new Date(filters.dateRange[1]))
    return missionNoOk && deviceOk && dateOk
  })
})

const cancelMission = async (row) => {
  await cancelMissionApi(row.id, row.device?.device_code || null)
  row.status = -1
  ElMessage.success(`任务 ${row.mission_no} 已撤销`)
}

const handleWsMessage = (message = {}) => {
  if (message.event === 'update_status') {
    const data = message.data || {}
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

  if (message.event === 'mission_completed') {
    const data = message.data || {}
    const target = missions.value.find((item) => item.hardware_id === data.h_id)
    if (!target) return
    target.status = 2
    if (data.device) {
      target.device = {
        ...(target.device || {}),
        device_code: data.device,
      }
    }
  }
}

onMounted(async () => {
  await loadMissions()
  unsubscribeWs = deviceStore.subscribeWsMessages(handleWsMessage)
})

onBeforeUnmount(() => {
  if (unsubscribeWs) unsubscribeWs()
})
</script>

<template>
  <section class="rounded-[28px] bg-white p-5 shadow-panel">
    <div class="mb-5 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <div>
        <h2 class="text-xl font-semibold text-slate-700">任务调度管理</h2>
        <p class="mt-1 text-sm text-slate-500">按你当前后端 `MissionOutSchema` 展示任务路径、设备、硬件号与状态。</p>
      </div>
      <el-button type="primary" plain @click="loadMissions">刷新</el-button>
    </div>

    <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-4">
      <el-input v-model="filters.missionNo" placeholder="任务编号筛选" clearable />
      <el-input v-model="filters.deviceCode" placeholder="设备编号筛选" clearable />
      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
      />
      <el-button @click="filters.missionNo = ''; filters.deviceCode = ''; filters.dateRange = []">
        清空筛选
      </el-button>
    </div>

    <el-table :data="filteredMissions" v-loading="loading" border>
      <el-table-column prop="mission_no" label="任务号" min-width="220" />
      <el-table-column prop="hardware_id" label="硬件号" min-width="100" />
      <el-table-column label="搬运路径" min-width="220">
        <template #default="{ row }">{{ missionPath(row) }}</template>
      </el-table-column>
      <el-table-column label="执行设备" min-width="130">
        <template #default="{ row }">{{ row.device?.device_code || '--' }}</template>
      </el-table-column>
      <el-table-column label="当前状态" min-width="120">
        <template #default="{ row }">
          <el-tag :type="statusTypeMap[row.status] || 'info'">
            {{ statusTextMap[row.status] || '未知' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="180">
        <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 0" type="danger" link @click="cancelMission(row)">
            撤销任务
          </el-button>
          <span v-else class="text-slate-400">--</span>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
