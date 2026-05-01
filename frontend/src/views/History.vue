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

      <div class="filter-section">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="搜索">
            <el-input
              v-model="filterForm.search"
              placeholder="搜索文件名..."
              clearable
              @keyup.enter="applyFilters"
              style="width: 200px;"
            />
          </el-form-item>
          <el-form-item label="图表类型">
            <el-select
              v-model="filterForm.chart_type"
              placeholder="全部类型"
              clearable
              @change="applyFilters"
              style="width: 140px;"
            >
              <el-option label="折线图" value="line" />
              <el-option label="柱状图" value="bar" />
              <el-option label="散点图" value="scatter" />
              <el-option label="面积图" value="area" />
              <el-option label="饼图" value="pie" />
              <el-option label="热力图" value="heatmap" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              @change="handleDateRangeChange"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyFilters">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>

        <div class="batch-actions" v-if="selectedRecords.length > 0">
          <span style="margin-right: 10px;">已选择 {{ selectedRecords.length }} 项</span>
          <el-button type="danger" size="small" @click="showBatchDeleteConfirm">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
        </div>
      </div>

      <el-table
        :data="records"
        v-loading="loading"
        style="width: 100%"
        @selection-change="handleSelectionChange"
        :row-key="(row) => row.id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="file_name" label="文件名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="chart_type" label="图表类型" width="100">
          <template #default="scope">
            <el-tag :type="getChartTagType(scope.row.chart_type)" size="small">
              {{ getChartTypeName(scope.row.chart_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewRecord(scope.row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button type="danger" link @click="showDeleteConfirm(scope.row)">
              <el-icon><Delete /></el-icon>
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
        <el-descriptions-item label="图表类型">
          <el-tag :type="getChartTagType(currentRecord?.chart_type)">
            {{ getChartTypeName(currentRecord?.chart_type) }}
          </el-tag>
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
      <span v-if="!isBatchDelete">确定要删除此记录吗？此操作不可恢复。</span>
      <span v-else>确定要删除选中的 {{ selectedRecords.length }} 条记录吗？此操作不可恢复。</span>
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
import {
  Search,
  Refresh,
  Delete,
  View
} from '@element-plus/icons-vue'

const loading = ref(false)
const deleting = ref(false)
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const stats = ref({})
const selectedRecords = ref([])
const dateRange = ref([])
const isBatchDelete = ref(false)

const filterForm = ref({
  search: '',
  chart_type: null,
  date_from: null,
  date_to: null
})

const detailVisible = ref(false)
const currentRecord = ref(null)
const chartData = ref(null)
const chartRef = ref(null)
let chartInstance = null

const deleteConfirmVisible = ref(false)
const recordToDelete = ref(null)

const chartTypeMap = {
  line: '折线图',
  bar: '柱状图',
  scatter: '散点图',
  area: '面积图',
  pie: '饼图',
  heatmap: '热力图'
}

const getChartTypeName = (type) => {
  return chartTypeMap[type] || type
}

const getChartTagType = (type) => {
  const tagTypes = {
    line: 'primary',
    bar: 'success',
    scatter: 'info',
    area: 'warning',
    pie: 'danger',
    heatmap: ''
  }
  return tagTypes[type] || ''
}

const handleDateRangeChange = (val) => {
  if (val && val.length === 2) {
    filterForm.value.date_from = val[0]
    filterForm.value.date_to = val[1]
  } else {
    filterForm.value.date_from = null
    filterForm.value.date_to = null
  }
}

const applyFilters = () => {
  currentPage.value = 1
  fetchTotalCount()
  fetchRecords()
}

const resetFilters = () => {
  filterForm.value = {
    search: '',
    chart_type: null,
    date_from: null,
    date_to: null
  }
  dateRange.value = []
  currentPage.value = 1
  fetchTotalCount()
  fetchRecords()
}

const fetchStats = async () => {
  try {
    const response = await api.get('/history/statistics/summary')
    stats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchTotalCount = async () => {
  try {
    const params = {}
    if (filterForm.value.search) params.search = filterForm.value.search
    if (filterForm.value.chart_type) params.chart_type = filterForm.value.chart_type
    if (filterForm.value.date_from) params.date_from = filterForm.value.date_from
    if (filterForm.value.date_to) params.date_to = filterForm.value.date_to
    
    const response = await api.get('/history/count', { params })
    total.value = response.data.count
  } catch (error) {
    console.error('获取总数失败:', error)
  }
}

const fetchRecords = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    if (filterForm.value.search) params.search = filterForm.value.search
    if (filterForm.value.chart_type) params.chart_type = filterForm.value.chart_type
    if (filterForm.value.date_from) params.date_from = filterForm.value.date_from
    if (filterForm.value.date_to) params.date_to = filterForm.value.date_to
    
    const response = await api.get('/history/list', { params })
    records.value = response.data
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
  
  let option = {}
  const data = chartData.value
  
  if (data.chart_type === 'pie') {
    option = {
      title: {
        text: data.title || '历史分析图表',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: data.series.map(s => ({
        ...s,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }))
    }
  } else if (data.chart_type === 'heatmap') {
    option = {
      title: {
        text: data.title || '历史分析图表',
        left: 'center'
      },
      tooltip: {
        position: 'top'
      },
      animation: false,
      grid: {
        height: '50%',
        top: '10%'
      },
      xAxis: {
        type: 'category',
        data: data.x_axis,
        splitArea: {
          show: true
        },
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'category',
        data: data.y_axis,
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: Math.min(...data.data.map(d => d[2])),
        max: Math.max(...data.data.map(d => d[2])),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '5%'
      },
      series: [
        {
          name: data.title,
          type: 'heatmap',
          data: data.data,
          label: {
            show: true
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  } else if (data.chart_type === 'scatter') {
    option = {
      title: {
        text: data.title || '历史分析图表',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: data.series.map(s => s.name),
        bottom: 10
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: data.x_axis_type || 'category',
        data: data.x_axis,
        axisLabel: {
          rotate: 45,
          interval: Math.floor(data.x_axis.length / 10)
        }
      },
      yAxis: {
        type: 'value'
      },
      series: data.series
    }
  } else {
    const series = data.series.map((s) => ({
      name: s.name,
      type: data.chart_type === 'area' ? 'line' : data.chart_type,
      data: s.data,
      smooth: data.chart_type === 'area' ? true : (data.options?.smooth !== false),
      areaStyle: data.chart_type === 'area' ? {} : undefined,
      stack: s.stack
    }))
    
    option = {
      title: {
        text: data.title || '历史分析图表',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: data.chart_type === 'bar' ? 'shadow' : 'cross'
        }
      },
      legend: {
        data: data.series.map(s => s.name),
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
        data: data.x_axis,
        axisLabel: {
          rotate: 45,
          interval: Math.floor(data.x_axis.length / 10)
        }
      },
      yAxis: {
        type: 'value'
      },
      series: series
    }
  }
  
  chartInstance.setOption(option)
}

const showDeleteConfirm = (record) => {
  isBatchDelete.value = false
  recordToDelete.value = record
  deleteConfirmVisible.value = true
}

const showBatchDeleteConfirm = () => {
  isBatchDelete.value = true
  deleteConfirmVisible.value = true
}

const confirmDelete = async () => {
  if (isBatchDelete.value) {
    const ids = selectedRecords.value.map(r => r.id)
    deleting.value = true
    try {
      await api.post('/history/batch-delete', ids)
      ElMessage.success(`成功删除 ${ids.length} 条记录`)
      deleteConfirmVisible.value = false
      selectedRecords.value = []
      fetchStats()
      fetchTotalCount()
      fetchRecords()
    } catch (error) {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    } finally {
      deleting.value = false
    }
  } else {
    if (!recordToDelete.value) return
    
    deleting.value = true
    try {
      await api.delete(`/history/${recordToDelete.value.id}`)
      ElMessage.success('删除成功')
      deleteConfirmVisible.value = false
      fetchStats()
      fetchTotalCount()
      fetchRecords()
    } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    } finally {
      deleting.value = false
    }
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
    fetchTotalCount()
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

.filter-section {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 15px;
}

.batch-actions {
  padding: 10px 0;
  border-top: 1px solid #ebeef5;
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
