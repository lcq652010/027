<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <el-icon size="28"><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_records || 0 }}</div>
              <div class="stat-label">总分析记录</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
              <el-icon size="28"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.line_chart_count || 0 }}</div>
              <div class="stat-label">折线图分析</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <el-icon size="28"><DataBoard /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.bar_chart_count || 0 }}</div>
              <div class="stat-label">柱状图分析</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <el-icon size="28"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ authStore.username }}</div>
              <div class="stat-label">当前用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="action-card">
          <template #header>
            <span>快速操作</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="12">
              <router-link to="/upload">
                <div class="action-item">
                  <el-icon size="40" color="#667eea"><Upload /></el-icon>
                  <span>上传数据</span>
                  <p class="action-desc">上传 CSV 格式的空气质量数据</p>
                </div>
              </router-link>
            </el-col>
            <el-col :span="12">
              <router-link to="/analysis">
                <div class="action-item">
                  <el-icon size="40" color="#38ef7d"><DataAnalysis /></el-icon>
                  <span>数据分析</span>
                  <p class="action-desc">生成折线图或柱状图进行分析</p>
                </div>
              </router-link>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="guide-card">
          <template #header>
            <span>使用指南</span>
          </template>
          <el-timeline>
            <el-timeline-item title="注册登录">
              <p>创建账户并登录系统</p>
            </el-timeline-item>
            <el-timeline-item title="上传数据">
              <p>上传包含空气质量数据的 CSV 文件</p>
            </el-timeline-item>
            <el-timeline-item title="数据清洗">
              <p>系统自动处理缺失值和异常值</p>
            </el-timeline-item>
            <el-timeline-item title="生成图表">
              <p>选择指标生成折线图或柱状图</p>
            </el-timeline-item>
            <el-timeline-item title="保存记录">
              <p>保存分析结果，随时查看历史记录</p>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近分析记录</span>
              <router-link to="/history" style="color: #667eea; font-size: 14px;">查看全部</router-link>
            </div>
          </template>
          <el-table :data="recentRecords" v-loading="loading" style="width: 100%">
            <el-table-column prop="file_name" label="文件名" />
            <el-table-column prop="analysis_type" label="分析类型">
              <template #default="scope">
                <el-tag :type="scope.row.analysis_type === 'line' ? 'primary' : 'success'">
                  {{ scope.row.analysis_type === 'line' ? '折线图' : '柱状图' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chart_type" label="图表类型">
              <template #default="scope">
                {{ scope.row.chart_type === 'line' ? '折线图' : '柱状图' }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="recentRecords.length === 0 && !loading" description="暂无分析记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import {
  FolderOpened,
  TrendCharts,
  DataBoard,
  User,
  Upload,
  DataAnalysis
} from '@element-plus/icons-vue'

const authStore = useAuthStore()
const loading = ref(false)
const stats = ref({})
const recentRecords = ref([])

const fetchStats = async () => {
  try {
    const response = await api.get('/history/statistics/summary')
    stats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchRecentRecords = async () => {
  loading.value = true
  try {
    const response = await api.get('/history/list', {
      params: { limit: 5 }
    })
    recentRecords.value = response.data
  } catch (error) {
    console.error('获取历史记录失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchStats()
  fetchRecentRecords()
})
</script>

<style scoped>
.dashboard-container {
  padding: 0;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.action-card,
.guide-card {
  height: 100%;
}

.action-item {
  text-align: center;
  padding: 30px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #ebeef5;
}

.action-item:hover {
  background: #f5f7fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-item span {
  display: block;
  margin-top: 12px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.action-desc {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

a {
  text-decoration: none;
}
</style>
