<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h2>SmartCS 智能客服平台</h2>
          <p>企业级电商客服工作台</p>
        </div>
      </template>
      <el-tabs v-model="activeTab" :stretch="true">
        <el-tab-pane label="登录" name="login">
          <el-form ref="loginForm" :model="loginData" :rules="rules" label-position="top">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="loginData.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="loginData.password" type="password" show-password placeholder="请输入密码" @keyup.enter="handleLogin" />
            </el-form-item>
            <el-button type="primary" :loading="loading" block @click="handleLogin">登录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerData" :rules="regRules" label-position="top">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="registerData.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="姓名" prop="display_name">
              <el-input v-model="registerData.display_name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerData.password" type="password" show-password placeholder="至少6位" />
            </el-form-item>
            <el-button type="success" :loading="loading" block @click="handleRegister">注册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <div class="demo-hint">
        <el-divider />
        <p style="color: #999; font-size: 12px;">
          测试账号：admin@smartcs.com / admin123
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)

const loginData = reactive({ email: 'admin@smartcs.com', password: 'admin123' })
const registerData = reactive({ email: '', display_name: '', password: '' })

const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const regRules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '至少6位', trigger: 'blur' }],
}

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginData.email, loginData.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  loading.value = true
  try {
    await auth.register(registerData.email, registerData.password, registerData.display_name)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginData.email = registerData.email
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card { width: 420px; }
.login-header { text-align: center; }
.login-header h2 { margin: 0; color: #333; }
.login-header p { margin: 5px 0 0; color: #999; font-size: 13px; }
.demo-hint { text-align: center; margin-top: 10px; }
</style>
