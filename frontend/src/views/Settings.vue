<template>
  <div class="settings-container">
    <el-card>
      <template #header>
        <span>用户设置</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="个人信息" name="profile">
          <el-form
            :model="profileForm"
            :rules="profileRules"
            ref="profileFormRef"
            label-width="100px"
            style="max-width: 500px;"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="姓名" prop="full_name">
              <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="authStore.isAdmin ? 'danger' : 'primary'">
                {{ authStore.isAdmin ? '管理员' : '普通用户' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="上次登录">
              <span>{{ formatDate(authStore.user?.last_login) || '无记录' }}</span>
            </el-form-item>
            <el-form-item label="注册时间">
              <span>{{ formatDate(authStore.user?.created_at) }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateProfile" :loading="updating">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <el-form
            :model="passwordForm"
            :rules="passwordRules"
            ref="passwordFormRef"
            label-width="100px"
            style="max-width: 500px;"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入原密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword" :loading="changing">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="关于" name="about">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="平台名称">
              空气质量数据分析平台
            </el-descriptions-item>
            <el-descriptions-item label="技术栈">
              前端：Vue 3 + ECharts + Element Plus<br />
              后端：Python FastAPI + SQLAlchemy + JWT
            </el-descriptions-item>
            <el-descriptions-item label="功能特性">
              <el-tag v-for="feature in features" :key="feature" style="margin: 5px;">
                {{ feature }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">
              v1.0.0
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const activeTab = ref('profile')
const updating = ref(false)
const changing = ref(false)

const profileForm = reactive({
  username: '',
  email: '',
  full_name: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const profileRules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const features = [
  '用户登录认证',
  'CSV 数据上传',
  '高级数据清洗',
  '多维度图表生成',
  '历史记录管理',
  '角色权限控制',
  'Token 刷新机制'
]

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const loadUserProfile = () => {
  if (authStore.user) {
    profileForm.username = authStore.user.username || ''
    profileForm.email = authStore.user.email || ''
    profileForm.full_name = authStore.user.full_name || ''
  }
}

const handleUpdateProfile = async () => {
  updating.value = true
  try {
    const updateData = {}
    if (profileForm.email !== undefined) updateData.email = profileForm.email || null
    if (profileForm.full_name !== undefined) updateData.full_name = profileForm.full_name || null
    
    await authStore.updateUser(updateData)
    ElMessage.success('个人信息更新成功')
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

const handleChangePassword = async () => {
  changing.value = true
  try {
    await authStore.changePassword(
      passwordForm.old_password,
      passwordForm.new_password
    )
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error) {
    console.error('密码修改失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('密码修改失败')
    }
  } finally {
    changing.value = false
  }
}

onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped>
.settings-container {
  max-width: 900px;
  margin: 0 auto;
}
</style>
