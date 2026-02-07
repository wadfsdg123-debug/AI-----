<template>
  <el-card class="task-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>最近审计任务</span>
        <el-button text type="primary" @click="$router.push('/audit')">
          查看全部
        </el-button>
      </div>
    </template>
    
    <el-table :data="tasks" style="width: 100%" v-loading="loading">
      <el-table-column prop="project_name" label="项目名称" min-width="120">
        <template #default="{ row }">
          <div class="project-name">
            <el-icon><folder /></el-icon>
            <span>{{ row.project_name }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="language" label="语言" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="getLangType(row.language)">
            {{ row.language }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="vulnerabilities" label="漏洞数" width="90" align="center">
        <template #default="{ row }">
          <span :class="['vuln-count', row.vulnerabilities > 0 ? 'has-vuln' : '']">
            {{ row.vulnerabilities }}
          </span>
        </template>
      </el-table-column>
      
      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button 
            link 
            type="primary" 
            size="small"
            @click="viewDetail(row.task_id)"
          >
            查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Folder } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const tasks = ref([])
const loading = ref(false)

const getLangType = (lang) => {
  const map = {
    'Python': 'success',
    'Java': 'danger',
    'PHP': 'primary',
    'JavaScript': 'warning'
  }
  return map[lang] || 'info'
}

const getStatusType = (status) => {
  const map = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    'pending': '等待中',
    'processing': '审计中',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/tasks/recent')
    tasks.value = res.data || []
  } catch (error) {
    console.error('获取任务列表失败:', error)
    // 使用模拟数据
    tasks.value = [
      { task_id: '1', project_name: 'web-project.zip', language: 'JavaScript', status: 'completed', vulnerabilities: 3, created_at: new Date() },
      { task_id: '2', project_name: 'backend-api.zip', language: 'Python', status: 'processing', vulnerabilities: 0, created_at: new Date() },
      { task_id: '3', project_name: 'user-service.zip', language: 'Java', status: 'completed', vulnerabilities: 12, created_at: new Date() }
    ]
  } finally {
    loading.value = false
  }
}

const viewDetail = (taskId) => {
  router.push(`/audit/${taskId}`)
}

onMounted(fetchTasks)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-name .el-icon {
  color: #409eff;
}

.vuln-count {
  font-weight: bold;
  color: #67c23a;
}

.vuln-count.has-vuln {
  color: #f56c6c;
}
</style>