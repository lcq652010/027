<template>
  <div class="history-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>历史分析记录</span>
          <el-statistic :value="stats.total_records || 0" style="display: inline-flex;">
            <template #suffix>
              <span style="font-size: 14px; color: #909399;">条记录</span>
            </template>
          </el-statistic>
        </div>
      </template>

      <el-table
        :data="records"
        v-loading="loading"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="file_name" label="文件名" show-overflow-tooltip />
        <el-table-column prop="analysis_type" label="分析类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.analysis_type === 'line' ? 'primary' : 'success'">
              {{ scope.row.analysis_type === 'line' ? '折线图' : '柱状图' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chart_type" label="图表类型" width="100">
          <template #default="scope">
            {{ scope.row.chart_type === 'line' ? '折线图' : '柱状图' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewRecord(scope.row)">
              查看
            </el-button>
            <el-button type="danger" link @click="deleteRecord(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchRecords"
          @current-change="fetchRecords"
        />
      </div>

      <el-empty v-if="records.length === 0 && !loading" description="暂无分析记录" />
    </el-card>

    <el-dialog
      v-model="detailVisible"
      title="记录详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ currentRecord?.id }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ currentRecord?.file_name }}</el-descriptions-item>
        <el-descriptions-item label="分析类型">
          <el-tag :type="currentRecord?.analysis_type === 'line' ? 'primary' : 'success'">
            {{ currentRecord?.analysis_type === 'line' ? '折线图' : '柱状图' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="图表类型">
          {{ currentRecord?.chart_type === 'line' ? '折线图' : '柱状图' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatDate(currentRecord?.created_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <div v-if="chartData" class="chart-wrapper">
        <div ref="chartRef" class="chart-container"></div>
      </div>
      <el-empty v-else description="暂无图表数据" />
    </el-dialog>

    <el-dialog
      v-model="deleteConfirmVisible"
      title="确认删除"
      width="400px"
    >
      <span>确定要删除选中的记录吗？此操作不可恢复。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteConfirmVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete" :loading="deleting">
            确定删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/utils/api'

const loading = ref(false)
const deleting = ref(false)
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const stats = ref({})
const selectedRecords = ref([])

const detailVisible = ref(false)
const currentRecord = ref(null)
const chartData = ref(null)
const chartRef = ref(null)
let chartInstance = null

const deleteConfirmVisible = ref(false)
const recordToDelete = ref(null)

const fetchStats = async () => {
  try {
    const response = await api.get('/history/statistics/summary')
    stats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchRecords = async () => {
  loading.value = true
  try {
    const response = await api.get('/history/list', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      }
    })
    records.value = response.data
    total.value = stats.value.total_records || response.data.length
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

const handleSelectionChange = (selection) => {
  selectedRecords.value = selection
}

const viewRecord = async (record) => {
  currentRecord.value = record
  detailVisible.value = true
  
  try {
    const response = await api.get(`/history/${record.id}`)
    if (response.data.chart_data) {
      chartData.value = JSON.parse(response.data.chart_data)
      setTimeout(() => renderChart(), 100)
    }
  } catch (error) {
    console.error('获取记录详情失败:', error)
  }
}

const renderChart = () => {
  if (!chartRef.value || !chartData.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  const series = chartData.value.series.map((s) => ({
    name: s.name,
    type: chartData.value.chart_type,
    data: s.data,
    smooth: chartData.value.chart_type === 'line'
  }))
  
  const option = {
    title: {
      text: chartData.value.title || '历史分析图表',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: chartData.value.series.map(s => s.name),
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.x_axis,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(chartData.value.x_axis.length / 10)
      }
    },
    yAxis: {
      type: 'value'
    },
    series: series
  }
  
  chartInstance.setOption(option)
}

const deleteRecord = (record) => {
  recordToDelete.value = record
  deleteConfirmVisible.value = true
}

const confirmDelete = async () => {
  if (!recordToDelete.value) return
  
  deleting.value = true
  try {
    await api.delete(`/history/${recordToDelete.value.id}`)
    ElMessage.success('删除成功')
    deleteConfirmVisible.value = false
    fetchStats()
    fetchRecords()
  } catch (error) {
    console.error('删除失败:', error)
  } finally {
    deleting.value = false
  }
}

watch(detailVisible, (val) => {
  if (!val && chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

onMounted(() => {
  fetchStats().then(() => {
    fetchRecords()
  })
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.chart-wrapper {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 450px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
