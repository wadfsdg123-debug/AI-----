<template>
  <div class="dashboard-container">
    <h1>仪表盘</h1>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6" v-for="stat in statistics" :key="stat.title">
        <el-card>
          <div class="stat-title">{{ stat.title }}</div>
          <div class="stat-value">{{ stat.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近任务 -->
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>最近任务</span>
          <el-button text type="primary" @click="refreshTasks">刷新</el-button>
        </div>
      </template>
      
      <el-table :data="tasks" v-loading="loading" style="width: 100%">
        <el-table-column prop="project_name" label="项目名称" min-width="150" />
        <el-table-column prop="language" label="语言" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.language }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="vulnerabilities" label="漏洞数" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'has-vuln': row.vulnerabilities > 0 }">
              {{ row.vulnerabilities }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <!-- 关键修复：跳转到 /audit/{task_id} -->
            <el-button 
              type="primary" 
              size="small"
              @click="viewAudit(row.task_id)"
            >
              查看审计
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()

const statistics = ref([
  { title: '总任务', value: 0 },
  { title: '总漏洞', value: 0 },
  { title: '已修复', value: 0 },
  { title: '平均时长', value: '0h' }
])
const tasks = ref([])
const loading = ref(false)

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const res = await axios.get('http://localhost:8000/api/dashboard/statistics')
    if (res.data) {
      statistics.value = [
        { title: '总任务', value: res.data.total_tasks || 0 },
        { title: '总漏洞', value: res.data.total_vulnerabilities || 0 },
        { title: '已修复', value: res.data.fixed_vulnerabilities || 0 },
        { title: '平均时长', value: (res.data.avg_processing_time || 0) + 'h' }
      ]
    }
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:8000/api/tasks/recent')
    if (Array.isArray(res.data)) {
      tasks.value = res.data
    } else {
      tasks.value = []
      console.error('任务列表格式错误:', res.data)
    }
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
    tasks.value = []
  } finally {
    loading.value = false
  }
}

// 刷新任务
const refreshTasks = () => {
  fetchStatistics()
  fetchTasks()
  ElMessage.success('已刷新')
}

// 关键修复：跳转到审计页面（不是 /terminal！）
const viewAudit = (taskId) => {
  console.log('跳转到审计页面:', taskId)
  router.push(`/audit/${taskId}`)
}

// 获取状态样式
const getStatusType = (status) => {
  const map = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return map[status] || 'info'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchStatistics()
  fetchTasks()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.stat-row {
  margin-bottom: 20px;
}
.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
.task-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.has-vuln {
  color: #f56c6c;
  font-weight: bold;
}
</style>