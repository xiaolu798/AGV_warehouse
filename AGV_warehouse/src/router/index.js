import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import MissionsView from '../views/MissionsView.vue'
import DevicesView from '../views/DevicesView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: LoginView, meta: { title: '登录', public: true, bare: true } },
    { path: '/dashboard', component: DashboardView, meta: { title: '实时大屏' } },
    { path: '/missions', component: MissionsView, meta: { title: '任务流水' } },
    { path: '/devices', component: DevicesView, meta: { title: '设备运维' } },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('agv_token')
  if (to.meta.public) {
    if (to.path === '/login' && token) return '/dashboard'
    return true
  }
  if (!token) return { path: '/login', query: { redirect: to.fullPath } }
  return true
})

router.afterEach((to) => {
  document.title = `AGV监控 - ${to.meta.title || '系统'}`
})

export default router
