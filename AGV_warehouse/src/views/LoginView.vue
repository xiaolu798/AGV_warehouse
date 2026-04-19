<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '../api/auth'

const router = useRouter()
const route = useRoute()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const formRef = ref()

const onSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await loginApi({
      username: form.username,
      password: form.password,
    })
    if (!data?.token) {
      ElMessage.error('登录失败，后端未返回 token')
      return
    }
    localStorage.setItem('agv_token', data.token)
    localStorage.setItem('agv_username', data.username || form.username)
    localStorage.setItem('agv_avatar', data.avatar || '')
    ElMessage.success(`欢迎回来，${data.username || form.username}`)
    const target = route.query.redirect || '/dashboard'
    router.push(String(target))
  } finally {
    loading.value = false
  }
}

const fillDemo = () => {
  form.username = 'admin'
  form.password = '123456'
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#1a2450] px-4">
    <div class="absolute -left-28 -top-24 h-72 w-72 rounded-full bg-purple-500/40 blur-3xl"></div>
    <div class="absolute -right-20 top-1/2 h-80 w-80 rounded-full bg-cyan-400/30 blur-3xl"></div>

    <div
      class="relative grid w-full max-w-6xl grid-cols-1 overflow-hidden rounded-[28px] border border-white/20 bg-white/10 shadow-2xl backdrop-blur-xl lg:grid-cols-2"
    >
      <div class="hidden bg-gradient-to-br from-[#4f56c7] via-[#6f63d6] to-[#ff83a8] p-10 text-white lg:block">
        <p class="text-sm uppercase tracking-[0.35em] text-white/80">AGV Warehouse</p>
        <h2 class="mt-4 text-4xl font-extrabold leading-tight">工业级设备监控平台</h2>
        <p class="mt-4 max-w-md text-white/90">
          对接你当前 FastAPI 后端，统一登录、设备监控、任务调度与运维处理。
        </p>

        <div class="mt-10 grid grid-cols-2 gap-4">
          <div class="rounded-2xl bg-white/20 p-4">
            <p class="text-xs text-white/80">登录方式</p>
            <p class="mt-1 text-3xl font-bold">JWT</p>
          </div>
          <div class="rounded-2xl bg-white/20 p-4">
            <p class="text-xs text-white/80">实时推送</p>
            <p class="mt-1 text-3xl font-bold">WebSocket</p>
          </div>
        </div>
      </div>

      <div class="bg-white p-8 sm:p-12">
        <h1 class="text-3xl font-bold text-slate-800">欢迎登录</h1>
        <p class="mt-2 text-sm text-slate-500">请输入账号密码，进入 AGV 仓储监控系统</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          class="mt-8"
          @keyup.enter="onSubmit"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="例如：admin" size="large" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="请输入密码"
              size="large"
            />
          </el-form-item>

          <div class="mt-2 flex gap-3">
            <el-button type="primary" size="large" class="flex-1" :loading="loading" @click="onSubmit">
              登录系统
            </el-button>
            <el-button size="large" @click="fillDemo">填充示例</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>
