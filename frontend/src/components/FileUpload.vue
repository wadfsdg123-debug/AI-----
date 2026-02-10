<template>
  <div class="upload-container">
    <!-- 上传区域 -->
    <div v-if="!uploadSuccess" class="cyber-upload-wrapper">
      <el-upload
        ref="uploadRef"
        drag
        :action="uploadUrl"
        :on-success="handleSuccess"
        :on-error="handleError"
        :before-upload="beforeUpload"
        :on-progress="handleProgress"
        accept=".zip"
        class="cyber-upload"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><upload-filled /></el-icon>
          <div class="upload-text">拖拽 ZIP 文件到这里</div>
          <div class="upload-subtext">或点击上传</div>
          <div class="upload-hint">
            支持 Python, Java, PHP, JavaScript | 最大 500MB
          </div>
        </div>
      </el-upload>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading && !uploadSuccess" class="cyber-card progress-area">
      <div class="progress-label">UPLOADING...</div>
      <el-progress 
        :percentage="uploadProgress" 
        :stroke-width="10"
        striped
        striped-flow
        class="cyber-progress-bar"
      />
      <div class="progress-percent">{{ uploadProgress }}%</div>
    </div>

    <!-- 上传成功 -->
    <div v-if="uploadSuccess" class="cyber-card success-area">
      <el-result
        icon="success"
        title="上传成功"
        :sub-title="`${uploadedFileName} | ${detectedType}`"
      >
        <template #extra>
          <el-button type="success" size="large" @click="startAudit" class="cyber-btn-primary">
            开始审计
          </el-button>
          <el-button size="large" @click="goToDashboard" class="cyber-btn-default">
            稍后处理
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { detectProjectType } from '../utils/projectDetector.js'

const router = useRouter()

const uploading = ref(false)
const uploadProgress = ref(0)
const uploadSuccess = ref(false)
const taskId = ref('')
const uploadedFileName = ref('')
const detectedType = ref('Unknown')
const fileList = ref([])

const uploadUrl = 'http://localhost:8000/api/upload'

const beforeUpload = (file) => {
  uploadedFileName.value = file.name
  
  if (!file.name.endsWith('.zip')) {
    ElMessage.error('仅支持 ZIP 格式')
    return false
  }
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.error('文件不能超过 500MB')
    return false
  }
  uploading.value = true
  uploadSuccess.value = false
  return true
}

const handleProgress = (event) => {
  uploadProgress.value = event.percent || 0
}

const handleSuccess = (response) => {
  uploading.value = false
  
  if (response.success && response.task_id) {
    taskId.value = response.task_id
    uploadedFileName.value = response.filename || uploadedFileName.value
    fileList.value = response.files || []
    detectedType.value = detectProjectType(fileList.value)
    uploadSuccess.value = true
    ElMessage.success('上传成功！请开始审计')
  } else {
    ElMessage.error(response.message || '上传失败')
    uploadSuccess.value = false
  }
}

const handleError = (error) => {
  uploading.value = false
  uploadSuccess.value = false
  console.error('上传错误:', error)
  ElMessage.error('上传失败，请检查后端服务')
}

const startAudit = async () => {
  try {
    await axios.post(`http://localhost:8000/api/tasks/${taskId.value}/start`)
    router.push({
      path: `/audit/${taskId.value}`,
      query: { type: detectedType.value, file: uploadedFileName.value }
    })
  } catch (error) {
    console.error('开始审计失败:', error)
    router.push({
      path: `/audit/${taskId.value}`,
      query: { type: detectedType.value, file: uploadedFileName.value }
    })
  }
}

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: 50px auto;
  padding: 20px;
}

/* 上传区域 */
.cyber-upload-wrapper {
  background: var(--bg-card);
  border: 2px solid var(--primary);
  border-radius: 8px;
  box-shadow: 0 0 20px var(--primary-glow);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.cyber-upload-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% { left: -100%; }
  100% { left: 100%; }
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  background: transparent;
  border: 2px dashed var(--border-color);
  border-radius: 6px;
  width: 100%;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--primary);
  background: rgba(0, 255, 159, 0.05);
}

.upload-content {
  text-align: center;
  pointer-events: none;
}

.upload-icon {
  font-size: 64px;
  color: var(--primary);
  margin-bottom: 20px;
  filter: drop-shadow(0 0 10px var(--primary-glow));
}

.upload-text {
  font-size: 24px;
  color: var(--primary);
  font-weight: bold;
  letter-spacing: 2px;
  margin-bottom: 10px;
  text-transform: uppercase;
}

.upload-subtext {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  display: inline-block;
}

/* 进度区域 */
.progress-area {
  padding: 40px;
  text-align: center;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.progress-label {
  color: var(--primary);
  font-size: 18px;
  letter-spacing: 4px;
  margin-bottom: 20px;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.progress-percent {
  color: var(--primary);
  font-size: 32px;
  font-weight: bold;
  margin-top: 20px;
  text-shadow: 0 0 10px var(--primary-glow);
}

:deep(.cyber-progress-bar .el-progress-bar__outer) {
  background-color: var(--bg-darker);
  border-radius: 5px;
}

:deep(.cyber-progress-bar .el-progress-bar__inner) {
  background: linear-gradient(90deg, var(--primary), var(--info));
  border-radius: 5px;
}

/* 成功区域 */
.success-area {
  background: var(--bg-card);
  border: 1px solid var(--primary);
  border-radius: 8px;
  box-shadow: 0 0 30px var(--primary-glow);
}

:deep(.el-result__title) {
  color: var(--primary);
  font-size: 28px;
  text-transform: uppercase;
  letter-spacing: 4px;
}

:deep(.el-result__subtitle) {
  color: var(--text-secondary);
  font-size: 16px;
  margin-top: 10px;
}

/* 按钮样式 */
.cyber-btn-primary {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: var(--bg-dark) !important;
  font-weight: bold;
  letter-spacing: 2px;
  text-transform: uppercase;
  clip-path: polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%);
  transition: all 0.3s;
}

.cyber-btn-primary:hover {
  box-shadow: 0 0 20px var(--primary-glow);
  transform: translateY(-2px);
}

.cyber-btn-default {
  background: transparent !important;
  border-color: var(--danger) !important;
  color: var(--danger) !important;
  font-weight: bold;
  letter-spacing: 2px;
  text-transform: uppercase;
  clip-path: polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%);
  transition: all 0.3s;
}

.cyber-btn-default:hover {
  background: var(--danger) !important;
  color: var(--bg-dark) !important;
  box-shadow: 0 0 20px var(--danger-glow);
}
</style>