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
        <el-tabs v-model="activeTab" class="config-tabs">
          <el-tab-pane label="图表配置" name="chart">
            <el-form :model="configForm" label-width="120px">
              <el-form-item label="图表类型">
                <el-select v-model="configForm.chartType" placeholder="请选择图表类型" style="width: 200px;">
                  <el-option label="折线图" value="line">
                    <span style="display: flex; align-items: center;">
                      <el-icon><TrendCharts /></el-icon>
                      <span style="margin-left: 8px;">折线图</span>
                    </span>
                  </el-option>
                  <el-option label="柱状图" value="bar">
                    <span style="display: flex; align-items: center;">
                      <el-icon><DataAnalysis /></el-icon>
                      <span style="margin-left: 8px;">柱状图</span>
                    </span>
                  </el-option>
                  <el-option label="散点图" value="scatter">
                    <span style="display: flex; align-items: center;">
                      <el-icon><Dot /></el-icon>
                      <span style="margin-left: 8px;">散点图</span>
                    </span>
                  </el-option>
                  <el-option label="面积图" value="area">
                    <span style="display: flex; align-items: center;">
                      <el-icon><PictureFilled /></el-icon>
                      <span style="margin-left: 8px;">面积图</span>
                    </span>
                  </el-option>
                  <el-option label="饼图" value="pie">
                    <span style="display: flex; align-items: center;">
                      <el-icon><PieChart /></el-icon>
                      <span style="margin-left: 8px;">饼图</span>
                    </span>
                  </el-option>
                  <el-option label="热力图" value="heatmap">
                    <span style="display: flex; align-items: center;">
                      <el-icon><Grid /></el-icon>
                      <span style="margin-left: 8px;">热力图</span>
                    </span>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="X轴列" v-if="columns.length > 0 && configForm.chartType !== 'heatmap'">
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
                  <el-option label="中位数" value="median" />
                  <el-option label="计数" value="count" />
                </el-select>
              </el-form-item>

              <el-form-item label="堆叠显示" v-if="configForm.chartType === 'area'">
                <el-switch v-model="configForm.stack" />
              </el-form-item>

              <el-form-item label="平滑曲线" v-if="configForm.chartType === 'line'">
                <el-switch v-model="configForm.smooth" />
              </el-form-item>

              <el-form-item label="点大小" v-if="configForm.chartType === 'scatter'">
                <el-slider v-model="configForm.symbolSize" :min="4" :max="20" style="width: 200px;" />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="generateChart" :loading="analyzing">
                  生成图表
                </el-button>
                <el-button @click="clearAll">清除</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="高级清洗配置" name="cleaning">
            <el-form :model="cleaningConfig" label-width="160px">
              <el-form-item label="缺失值处理策略">
                <el-select v-model="cleaningConfig.missingStrategy" style="width: 100%;">
                  <el-option label="平均值填充" value="mean" />
                  <el-option label="中位数填充（默认）" value="median" />
                  <el-option label="众数填充" value="mode" />
                  <el-option label="前向填充" value="ffill" />
                  <el-option label="后向填充" value="bfill" />
                  <el-option label="删除包含缺失值的行" value="drop" />
                  <el-option label="常量填充" value="constant" />
                </el-select>
              </el-form-item>

              <el-form-item label="常量填充值" v-if="cleaningConfig.missingStrategy === 'constant'">
                <el-input-number v-model="cleaningConfig.constantValue" :step="0.1" />
              </el-form-item>

              <el-form-item label="异常值处理方法">
                <el-select v-model="cleaningConfig.outlierMethod" style="width: 100%;">
                  <el-option label="IQR 方法（默认）" value="iqr" />
                  <el-option label="Z-Score 方法" value="zscore" />
                  <el-option label="不处理异常值" value="none" />
                </el-select>
              </el-form-item>

              <el-form-item label="IQR 阈值系数" v-if="cleaningConfig.outlierMethod === 'iqr'">
                <el-slider v-model="cleaningConfig.outlierThreshold" :min="1.0" :max="3.0" :step="0.1" style="width: 300px;" />
                <span style="margin-left: 10px;">{{ cleaningConfig.outlierThreshold }}</span>
              </el-form-item>

              <el-form-item label="Z-Score 阈值" v-if="cleaningConfig.outlierMethod === 'zscore'">
                <el-slider v-model="cleaningConfig.zscoreThreshold" :min="2.0" :max="5.0" :step="0.5" style="width: 300px;" />
                <span style="margin-left: 10px;">{{ cleaningConfig.zscoreThreshold }}</span>
              </el-form-item>

              <el-form-item label="移除重复行">
                <el-switch v-model="cleaningConfig.removeDuplicates" />
              </el-form-item>

              <el-form-item>
                <el-button type="success" @click="validateData" :loading="validating">
                  验证数据质量
                </el-button>
              </el-form-item>
            </el-form>

            <el-divider v-if="validationResult" />

            <div v-if="validationResult" class="validation-result">
              <h4>数据质量验证结果</h4>
              
              <el-alert
                v-if="validationResult.is_valid"
                :title="'验证通过：' + (validationResult.issues?.length || 0) + ' 个问题'"
                type="success"
                :closable="false"
                style="margin-bottom: 15px;"
              />
              <el-alert
                v-else
                :title="'验证失败：' + (validationResult.issues?.length || 0) + ' 个问题'"
                type="error"
                :closable="false"
                style="margin-bottom: 15px;"
              />

              <el-alert
                v-for="(issue, idx) in validationResult.issues"
                :key="'issue-' + idx"
                :title="issue"
                type="error"
                :closable="false"
                style="margin-bottom: 10px;"
              />

              <el-alert
                v-for="(warning, idx) in validationResult.warnings"
                :key="'warning-' + idx"
                :title="warning"
                type="warning"
                :closable="false"
                style="margin-bottom: 10px;"
              />

              <div v-if="validationResult.info" class="data-info">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item 
                    v-for="(info, key) in validationResult.info[0]" 
                    :key="key"
                    :label="key"
                  >
                    <template v-if="Array.isArray(info)">
                      <el-tag v-for="(item, i) in info.slice(0, 5)" :key="i" style="margin-right: 5px; margin-bottom: 5px;" size="small">
                        {{ item }}
                      </el-tag>
                      <span v-if="info.length > 5" style="color: #909399;">... 等 {{ info.length }} 项</span>
                    </template>
                    <template v-else>{{ info }}</template>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>

    <el-card v-if="chartData" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>{{ chartData.title || '图表' }}</span>
          <div class="chart-actions">
            <el-button type="primary" size="small" @click="saveRecord" :loading="saving">
              保存记录
            </el-button>
          </div>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
      
      <el-divider v-if="statistics && Object.keys(statistics.statistics || {}).length > 0" />
      
      <div v-if="statistics && Object.keys(statistics.statistics || {}).length > 0" class="statistics-section">
        <h3>数据统计</h3>
        <el-row :gutter="20">
          <el-col :span="6" v-for="(stat, colName) in statistics.statistics" :key="colName" style="margin-bottom: 20px;">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-name">{{ colName }}</div>
                <el-divider />
                <div class="stat-detail">
                  <div class="stat-row"><span class="stat-label">均值:</span><span class="stat-value">{{ stat.mean }}</span></div>
                  <div class="stat-row"><span class="stat-label">中位数:</span><span class="stat-value">{{ stat.median }}</span></div>
                  <div class="stat-row"><span class="stat-label">标准差:</span><span class="stat-value">{{ stat.std }}</span></div>
                  <div class="stat-row"><span class="stat-label">最小:</span><span class="stat-value">{{ stat.min }}</span></div>
                  <div class="stat-row"><span class="stat-label">最大:</span><span class="stat-value">{{ stat.max }}</span></div>
                  <div class="stat-row" v-if="stat.missing_count > 0">
                    <span class="stat-label">缺失:</span>
                    <span class="stat-value" style="color: #f56c6c;">{{ stat.missing_count }} ({{ stat.missing_percent }}%)</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-divider v-if="statistics.correlation && Object.keys(statistics.correlation).length > 0" />

        <div v-if="statistics.correlation && Object.keys(statistics.correlation).length > 0" class="correlation-section">
          <h3>相关性矩阵</h3>
          <el-table :data="correlationTableData" border size="small">
            <el-table-column label="变量" prop="variable" fixed />
            <el-table-column
              v-for="col in correlationColumns"
              :key="col"
              :label="col"
              :prop="col"
            >
              <template #default="scope">
                <span :class="getCorrelationClass(scope.row[col])">
                  {{ scope.row[col]?.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/utils/api'
import { 
  UploadFilled, 
  TrendCharts, 
  DataAnalysis, 
  Dot, 
  PictureFilled, 
  PieChart,
  Grid
} from '@element-plus/icons-vue'

const uploadRef = ref(null)
const chartRef = ref(null)
const currentFile = ref(null)
const analyzing = ref(false)
const saving = ref(false)
const validating = ref(false)
const columns = ref([])
const numericColumns = ref([])
const chartData = ref(null)
const statistics = ref(null)
const validationResult = ref(null)
const activeTab = ref('chart')
let chartInstance = null

const configForm = reactive({
  chartType: 'line',
  xColumn: '',
  yColumns: [],
  title: '空气质量分析',
  aggregate: 'mean',
  stack: false,
  smooth: true,
  symbolSize: 8
})

const cleaningConfig = reactive({
  missingStrategy: 'median',
  outlierMethod: 'iqr',
  removeDuplicates: true,
  constantValue: 0,
  outlierThreshold: 1.5,
  zscoreThreshold: 3.0
})

const correlationColumns = computed(() => {
  if (!statistics.value?.correlation) return []
  return Object.keys(statistics.value.correlation)
})

const correlationTableData = computed(() => {
  if (!statistics.value?.correlation) return []
  const corr = statistics.value.correlation
  const cols = Object.keys(corr)
  return cols.map(col => {
    const row = { variable: col }
    cols.forEach(c => {
      row[c] = corr[col]?.[c]
    })
    return row
  })
})

const getCorrelationClass = (value) => {
  if (value === undefined || value === null) return ''
  const absVal = Math.abs(value)
  if (absVal >= 0.8) return 'correlation-strong'
  if (absVal >= 0.5) return 'correlation-medium'
  if (absVal >= 0.3) return 'correlation-weak'
  return 'correlation-none'
}

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
  validationResult.value = null
  configForm.chartType = 'line'
  configForm.xColumn = ''
  configForm.yColumns = []
  configForm.title = '空气质量分析'
  configForm.aggregate = 'mean'
  configForm.stack = false
  configForm.smooth = true
  configForm.symbolSize = 8
  cleaningConfig.missingStrategy = 'median'
  cleaningConfig.outlierMethod = 'iqr'
  cleaningConfig.removeDuplicates = true
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

const validateData = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请先上传文件')
    return
  }

  validating.value = true
  const formData = new FormData()
  formData.append('file', currentFile.value)

  try {
    const response = await api.post('/data/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    validationResult.value = response.data.validation
    if (statistics.value) {
      statistics.value = response.data.statistics
    }
    ElMessage.success('数据验证完成')
  } catch (error) {
    console.error('数据验证失败:', error)
  } finally {
    validating.value = false
  }
}

const generateChart = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请先上传文件')
    return
  }
  if (configForm.chartType !== 'heatmap' && !configForm.xColumn) {
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
  formData.append('chart_type', configForm.chartType)
  formData.append('x_column', configForm.xColumn)
  formData.append('y_columns', configForm.yColumns.join(','))
  formData.append('title', configForm.title)
  formData.append('aggregate', configForm.aggregate)
  formData.append('stack', configForm.stack)
  formData.append('smooth', configForm.smooth)

  try {
    const response = await api.post('/data/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
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
  
  let option = {}
  
  if (data.chart_type === 'pie') {
    option = {
      title: {
        text: data.title,
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
        text: data.title,
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
        text: data.title,
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
      smooth: data.chart_type === 'area' ? true : configForm.smooth,
      areaStyle: data.chart_type === 'area' ? {} : undefined,
      stack: s.stack
    }))
    
    option = {
      title: {
        text: data.title,
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
      analysis_config: JSON.stringify({
        ...configForm,
        ...cleaningConfig
      })
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

.config-tabs {
  margin-bottom: 20px;
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

.validation-result {
  margin-top: 20px;
}

.validation-result h4 {
  margin-bottom: 15px;
  color: #303133;
}

.data-info {
  margin-top: 15px;
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

.stat-row {
  display: flex;
  justify-content: space-between;
}

.stat-label {
  color: #909399;
}

.stat-value {
  font-weight: 500;
}

.correlation-section {
  margin-top: 20px;
}

.correlation-section h3 {
  margin-bottom: 15px;
  color: #303133;
}

.correlation-strong {
  color: #f56c6c;
  font-weight: bold;
}

.correlation-medium {
  color: #e6a23c;
  font-weight: 500;
}

.correlation-weak {
  color: #409eff;
}

.correlation-none {
  color: #909399;
}
</style>
