<template>
  <div class="upload-container">
    <el-upload
      ref="uploadRef"
      drag
      :action="uploadUrl"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :on-progress="handleProgress"
      accept=".zip"
    >
      <el-icon class="upload-icon"><upload-filled /></el-icon>
      <div class="upload-text">
        拖拽 ZIP 文件到这里，或 <em>点击上传</em>
      </div>
      <div class="upload-hint">
        支持 Python, Java, PHP, JavaScript 项目（最大 500MB）
      </div>
    </el-upload>

    <div v-if="uploading" class="progress-wrapper">
      <el-progress :percentage="uploadProgress" striped striped-flow />
      <div class="progress-text">上传中 {{ uploadProgress }}%</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const router = useRouter()
const uploading = ref(false)
const uploadProgress = ref(0)

const uploadUrl = 'http://localhost:8000/api/upload'

const beforeUpload = (file) => {
  if (!file.name.endsWith('.zip')) {
    ElMessage.error('仅支持 ZIP 格式')
    return false
  }
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.error('文件不能超过 500MB')
    return false
  }
  uploading.value = true
  return true
}

const handleProgress = (event) => {
  uploadProgress.value = event.percent || 0
}

const handleSuccess = (response) => {
  uploading.value = false
  console.log('上传响应:', response)  // 调试用
  
  if (response.success && response.task_id) {
    ElMessage.success('上传成功，开始审计...')
    // 关键：确保跳转到 /audit/{task_id}
    const targetUrl = `/audit/${response.task_id}`
    console.log('跳转到:', targetUrl)  // 调试用
    router.push(targetUrl)
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleError = (error) => {
  uploading.value = false
  console.error('上传错误:', error)
  ElMessage.error('上传失败，请检查网络')
}
</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px;
}
.upload-icon {
  font-size: 48px;
  color: #409eff;
}
.upload-text {
  font-size: 16px;
  margin: 10px 0;
}
.upload-hint {
  font-size: 12px;
  color: #999;
}
.progress-wrapper {
  margin-top: 20px;
}
</style>