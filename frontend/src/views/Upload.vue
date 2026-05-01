<template>
  <div class="upload-container">
    <el-card>
      <template #header>
        <span>数据上传与清洗</span>
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
            只能上传 CSV 格式文件
          </div>
        </template>
      </el-upload>

      <div v-if="fileList.length > 0" class="file-info">
        <el-descriptions title="文件信息" :column="2" border>
          <el-descriptions-item label="文件名">{{ fileList[0].name }}</el-descriptions-item>
          <el-descriptions-item label="文件大小">{{ formatFileSize(fileList[0].size) }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider v-if="fileList.length > 0" />

      <div v-if="fileList.length > 0" class="action-buttons">
        <el-button type="primary" @click="uploadAndClean" :loading="uploading">
          上传并清洗数据
        </el-button>
        <el-button @click="clearFile">清除文件</el-button>
      </div>

      <el-divider v-if="cleaningResult" />

      <div v-if="cleaningResult" class="cleaning-result">
        <h3>数据清洗结果</h3>
        
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="8">
            <el-statistic title="原始数据行数" :value="cleaningResult.original_rows" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="清洗后行数" :value="cleaningResult.cleaned_rows" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="移除行数" :value="cleaningResult.removed_rows">
              <template #suffix>
                <span style="color: #f56c6c;">行</span>
              </template>
            </el-statistic>
          </el-col>
        </el-row>

        <el-divider />

        <h4>数据列：</h4>
        <el-tag
          v-for="col in cleaningResult.columns"
          :key="col"
          style="margin-right: 10px; margin-bottom: 10px;"
        >
          {{ col }}
        </el-tag>

        <el-divider />

        <h4>数据预览（前10行）：</h4>
        <el-table :data="cleaningResult.sample_data" border max-height="400">
          <el-table-column
            v-for="col in cleaningResult.columns"
            :key="col"
            :prop="col"
            :label="col"
            :width="150"
            show-overflow-tooltip
          />
        </el-table>

        <div class="next-step">
          <el-button type="primary" size="large" @click="goToAnalysis">
            前往数据分析
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { UploadFilled, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)
const cleaningResult = ref(null)
const currentFile = ref(null)

const handleFileChange = (file) => {
  if (!file.name.endsWith('.csv')) {
    ElMessage.error('只能上传 CSV 格式文件')
    return
  }
  currentFile.value = file.raw
  fileList.value = [file]
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const clearFile = () => {
  fileList.value = []
  cleaningResult.value = null
  currentFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const uploadAndClean = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  const formData = new FormData()
  formData.append('file', currentFile.value)

  try {
    const response = await api.post('/data/clean', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    cleaningResult.value = response.data
    ElMessage.success('数据清洗完成')
  } catch (error) {
    console.error('数据清洗失败:', error)
  } finally {
    uploading.value = false
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const goToAnalysis = () => {
  router.push('/analysis')
}
</script>

<style scoped>
.upload-container {
  max-width: 1000px;
  margin: 0 auto;
}

.upload-dragger {
  width: 100% !important;
}

.file-info {
  margin-top: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.cleaning-result {
  margin-top: 20px;
}

.cleaning-result h3 {
  margin-bottom: 15px;
  color: #303133;
}

.cleaning-result h4 {
  margin: 15px 0 10px;
  color: #606266;
}

.next-step {
  margin-top: 30px;
  text-align: center;
}
</style>
