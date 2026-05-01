<template>
  <div class="analysis-container">
    <el-card>
      <template #header>
        <span>数据分析</span>
      </template>
      
      <el-upload
        ref="uploadRef"
        class="upload-dragger"
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :limit="1"
        accept=".csv"
      >
        <el-icon class="el-icon--upload" size="48"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            上传 CSV 格式的空气质量数据进行分析
          </div>
        </template>
      </el-upload>

      <el-divider v-if="currentFile" />

      <div v-if="currentFile" class="analysis-config">
        <el-form :model="configForm" label-width="120px">
          <el-form-item label="图表类型">
            <el-radio-group v-model="configForm.chartType">
              <el-radio value="line">折线图</el-radio>
              <el-radio value="bar">柱状图</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="X轴列" v-if="columns.length > 0">
            <el-select v-model="configForm.xColumn" placeholder="请选择X轴列" style="width: 300px;">
              <el-option
                v-for="col in columns"
                :key="col"
                :label="col"
                :value="col"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="Y轴列" v-if="numericColumns.length > 0">
            <el-select
              v-model="configForm.yColumns"
              multiple
              placeholder="请选择Y轴列（可多选）"
              style="width: 100%;"
            >
              <el-option
                v-for="col in numericColumns"
                :key="col"
                :label="col"
                :value="col"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="图表标题">
            <el-input
              v-model="configForm.title"
              placeholder="请输入图表标题"
              style="width: 300px;"
            />
          </el-form-item>

          <el-form-item label="聚合方式" v-if="configForm.chartType === 'bar'">
            <el-select v-model="configForm.aggregate" placeholder="请选择聚合方式" style="width: 200px;">
              <el-option label="平均值" value="mean" />
              <el-option label="求和" value="sum" />
              <el-option label="最大值" value="max" />
              <el-option label="最小值" value="min" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="generateChart" :loading="analyzing">
              生成图表
            </el-button>
            <el-button @click="clearAll">清除</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card v-if="chartData" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>{{ chartData.title || '图表' }}</span>
          <el-button type="primary" size="small" @click="saveRecord" :loading="saving">
            保存记录
          </el-button>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
      
      <el-divider v-if="statistics" />
      
      <div v-if="statistics" class="statistics-section">
        <h3>数据统计</h3>
        <el-row :gutter="20">
          <el-col :span="6" v-for="(stat, colName) in statistics.statistics" :key="colName">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-name">{{ colName }}</div>
                <el-divider />
                <div class="stat-detail">
                  <div>均值: {{ stat.mean }}</div>
                  <div>中位数: {{ stat.median }}</div>
                  <div>标准差: {{ stat.std }}</div>
                  <div>最小: {{ stat.min }}</div>
                  <div>最大: {{ stat.max }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/utils/api'
import { UploadFilled } from '@element-plus/icons-vue'

const uploadRef = ref(null)
const chartRef = ref(null)
const currentFile = ref(null)
const analyzing = ref(false)
const saving = ref(false)
const columns = ref([])
const numericColumns = ref([])
const chartData = ref(null)
const statistics = ref(null)
let chartInstance = null

const configForm = reactive({
  chartType: 'line',
  xColumn: '',
  yColumns: [],
  title: '空气质量分析',
  aggregate: 'mean'
})

const handleFileChange = async (file) => {
  if (!file.name.endsWith('.csv')) {
    ElMessage.error('只能上传 CSV 格式文件')
    return
  }
  currentFile.value = file.raw
  
  const formData = new FormData()
  formData.append('file', currentFile.value)
  
  try {
    const response = await api.post('/data/statistics', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    statistics.value = response.data
    columns.value = response.data.columns
    numericColumns.value = response.data.numeric_columns
    
    if (columns.value.length > 0) {
      const timeColumns = columns.value.filter(c => 
        c.toLowerCase().includes('time') || 
        c.toLowerCase().includes('date')
      )
      configForm.xColumn = timeColumns.length > 0 ? timeColumns[0] : columns.value[0]
    }
    
    if (numericColumns.value.length > 0) {
      configForm.yColumns = numericColumns.value.slice(0, 3)
    }
  } catch (error) {
    console.error('获取数据统计失败:', error)
  }
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const clearAll = () => {
  currentFile.value = null
  columns.value = []
  numericColumns.value = []
  chartData.value = null
  statistics.value = null
  configForm.chartType = 'line'
  configForm.xColumn = ''
  configForm.yColumns = []
  configForm.title = '空气质量分析'
  configForm.aggregate = 'mean'
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

const generateChart = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请先上传文件')
    return
  }
  if (!configForm.xColumn) {
    ElMessage.warning('请选择X轴列')
    return
  }
  if (configForm.yColumns.length === 0) {
    ElMessage.warning('请至少选择一个Y轴列')
    return
  }

  analyzing.value = true
  const formData = new FormData()
  formData.append('file', currentFile.value)

  try {
    let response
    if (configForm.chartType === 'line') {
      response = await api.post('/data/analyze/line', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: {
          x_column: configForm.xColumn,
          y_columns: configForm.yColumns.join(','),
          title: configForm.title
        }
      })
    } else {
      response = await api.post('/data/analyze/bar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: {
          x_column: configForm.xColumn,
          y_columns: configForm.yColumns.join(','),
          title: configForm.title,
          aggregate: configForm.aggregate
        }
      })
    }
    
    chartData.value = response.data
    renderChart(response.data)
    ElMessage.success('图表生成成功')
  } catch (error) {
    console.error('生成图表失败:', error)
  } finally {
    analyzing.value = false
  }
}

const renderChart = (data) => {
  if (!chartRef.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  const series = data.series.map((s, index) => ({
    name: s.name,
    type: data.chart_type,
    data: s.data,
    smooth: data.chart_type === 'line',
    symbol: 'circle',
    symbolSize: 6
  }))
  
  const option = {
    title: {
      text: data.title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: data.chart_type === 'line' ? 'cross' : 'shadow'
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
  
  chartInstance.setOption(option)
  
  const handleResize = () => {
    chartInstance?.resize()
  }
  window.addEventListener('resize', handleResize)
}

const saveRecord = async () => {
  if (!chartData.value || !currentFile.value) {
    ElMessage.warning('请先生成图表')
    return
  }

  saving.value = true
  try {
    await api.post('/history/save', {
      file_name: currentFile.value.name,
      analysis_type: configForm.chartType,
      chart_type: configForm.chartType,
      chart_data: JSON.stringify(chartData.value),
      analysis_config: JSON.stringify(configForm)
    })
    ElMessage.success('记录保存成功')
  } catch (error) {
    console.error('保存记录失败:', error)
  } finally {
    saving.value = false
  }
}

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.analysis-container {
  max-width: 1200px;
  margin: 0 auto;
}

.upload-dragger {
  width: 100% !important;
}

.analysis-config {
  margin-top: 20px;
}

.chart-container {
  width: 100%;
  height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.statistics-section {
  margin-top: 20px;
}

.statistics-section h3 {
  margin-bottom: 20px;
  color: #303133;
}

.stat-item {
  text-align: center;
}

.stat-name {
  font-size: 16px;
  font-weight: bold;
  color: #667eea;
}

.stat-detail {
  text-align: left;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
