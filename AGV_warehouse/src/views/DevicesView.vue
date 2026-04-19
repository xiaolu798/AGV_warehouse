<script setup>
import { computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useDeviceStore } from '../stores/device'

const deviceStore = useDeviceStore()

const statusTextMap = {
  0: '空闲',
  1: '忙碌',
  2: '故障',
}

const statusOptions = [
  { label: '空闲', value: 0 },
  { label: '忙碌', value: 1 },
  { label: '故障', value: 2 },
]

const rows = computed(() => deviceStore.sortedDevices)

const handleStatusChange = async (row, status) => {
  await deviceStore.setDeviceStatus(row, status)
}

const handleReset = async (row) => {
  await deviceStore.resetDevice(row)
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定停用设备 ${row.device_code} ?`, '提示', { type: 'warning' })
  await deviceStore.removeDevice(row)
}

onMounted(() => {
  if (!deviceStore.devices.length) {
    deviceStore.loadDevices()
  }
})
</script>

<template>
  <section class="rounded-2xl bg-white p-5 shadow-panel">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-700">设备运维配置</h2>
      <el-button type="primary" plain @click="deviceStore.loadDevices()">刷新</el-button>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="device_code" label="设备编号" min-width="120" />
      <el-table-column label="当前状态" min-width="110">
        <template #default="{ row }">{{ statusTextMap[row.work_status] || '未知' }}</template>
      </el-table-column>
      <el-table-column label="状态切换" min-width="160">
        <template #default="{ row }">
          <el-select
            :model-value="row.work_status"
            placeholder="切换状态"
            class="w-full"
            @change="(value) => handleStatusChange(row, value)"
          >
            <el-option
              v-for="opt in statusOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="IP 地址" min-width="150">
        <template #default="{ row }">{{ row.ip_addr || '--' }}</template>
      </el-table-column>
      <el-table-column label="固件版本" min-width="120">
        <template #default="{ row }">{{ row.firmware || '--' }}</template>
      </el-table-column>
      <el-table-column label="总里程(km)" min-width="120">
        <template #default="{ row }">{{ row.mileage || 0 }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="success" link @click="handleReset(row)">复位</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除/停用</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
