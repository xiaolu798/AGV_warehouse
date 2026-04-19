<script setup>
import { computed, onMounted, onBeforeUnmount, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDeviceStore } from './stores/device'

const route = useRoute()
const router = useRouter()
const deviceStore = useDeviceStore()
const realtimeStarted = ref(false)

const menus = [
  { path: '/dashboard', label: '实时大屏' },
  { path: '/missions', label: '任务流水' },
  { path: '/devices', label: '设备运维' },
]

const activeMenu = computed(() => route.path)
const isBarePage = computed(() => Boolean(route.meta?.bare))

const goto = (path) => {
  if (route.path !== path) router.push(path)
}

const ensureRealtime = async () => {
  const token = localStorage.getItem('agv_token')
  if (!token || realtimeStarted.value) return
  await deviceStore.initRealtime()
  realtimeStarted.value = true
}

onMounted(async () => {
  await ensureRealtime()
})

watch(
  () => route.path,
  async () => {
    await ensureRealtime()
  },
)

const logout = async () => {
  localStorage.removeItem('agv_token')
  realtimeStarted.value = false
  deviceStore.disconnectWs()
  await router.push('/login')
}

onBeforeUnmount(() => {
  deviceStore.disconnectWs()
})
</script>

<template>
  <div v-if="isBarePage" class="min-h-screen bg-slate-100">
    <router-view />
  </div>
  <div v-else class="min-h-screen bg-slate-100">
    <div class="mx-auto flex min-h-screen max-w-[1800px]">
      <aside class="w-[220px] border-r border-slate-200 bg-[#0f4c81] p-5 text-white">
        <div class="mb-8 rounded-xl bg-white/10 p-4">
          <h1 class="text-lg font-bold">AGV 监控中心</h1>
          <p class="mt-2 text-xs text-cyan-100">工业级仓储调度前端</p>
        </div>
        <nav class="space-y-2">
          <button
            v-for="item in menus"
            :key="item.path"
            class="w-full rounded-lg px-3 py-2 text-left transition"
            :class="
              activeMenu === item.path
                ? 'bg-white text-[#0f4c81] shadow'
                : 'bg-white/5 text-slate-100 hover:bg-white/20'
            "
            @click="goto(item.path)"
          >
            {{ item.label }}
          </button>
          <button
            class="w-full rounded-lg bg-red-500/80 px-3 py-2 text-left text-white transition hover:bg-red-500"
            @click="logout"
          >
            退出登录
          </button>
        </nav>
      </aside>
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>
