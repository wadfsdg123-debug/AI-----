<template>
  <div class="dashboard-page">
    <!-- 头部 -->
    <div class="dashboard-header">
      <h1 class="glitch" data-text="SYSTEM DASHBOARD">SYSTEM DASHBOARD</h1>
      <div class="header-line"></div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div 
        v-for="stat in computedStatistics" 
        :key="stat.title"
        class="cyber-card stat-card"
        :class="stat.class"
      >
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-title">{{ stat.title }}</div>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="cyber-card tasks-section">
      <div class="section-header">
        <h2 class="section-title">>> RECENT_TASKS</h2>
        <button class="refresh-btn" @click="refreshTasks">
          [ REFRESH ]
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>LOADING DATA...</span>
      </div>

      <div v-else-if="tasks.length === 0" class="empty-state">
        <div class="empty-icon">◉</div>
        <p>NO TASKS FOUND</p>
        <button class="cyber-button" @click="$router.push('/')">
          [ UPLOAD FILE ]
        </button>
      </div>

      <div v-else class="tasks-table">
        <!-- 表头 -->
        <div class="table-header">
          <div class="col-file">文件名</div>
          <div class="col-lang">语言</div>
          <div class="col-status">状态</div>
          <div class="col-vulns">漏洞数</div>
          <div class="col-time">创建时间</div>
          <div class="col-action">操作</div>
        </div>

        <!-- 任务行 -->
        <div 
          v-for="task in tasks" 
          :key="task.task_id"
          class="task-row"
          :class="'status-' + task.status"
        >
          <div class="col-file">
            <div class="file-name">{{ task.filename }}</div>
            <div class="file-id">ID: {{ task.task_id }}</div>
          </div>
          
          <div class="col-lang">
            <span class="lang-tag" :class="'lang-' + getLangClass(task.project_type)">
              {{ task.project_type }}
            </span>
          </div>
          
          <div class="col-status">
            <span class="status-badge" :class="task.status">
              {{ getStatusText(task.status) }}
            </span>
          </div>
          
          <div class="col-vulns">
            <span class="vuln-count" :class="{ 'has-vuln': task.vulnerabilities > 0 }">
              {{ task.vulnerabilities }}
            </span>
          </div>
          
          <div class="col-time">
            {{ formatTime(task.created_at) }}
          </div>
          
          <div class="col-action">
            <button 
              v-if="task.status === 'pending'"
              class="action-btn start"
              @click="startAudit(task)"
            >
              开始审计
            </button>
            <button 
              v-else-if="task.status === 'processing'"
              class="action-btn view"
              @click="viewAudit(task)"
            >
              查看进度
            </button>
            <button 
              v-else
              class="action-btn report"
              @click="viewAudit(task)"
            >
              查看审计
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()

const tasks = ref([])
const loading = ref(false)

const computedStatistics = computed(() => {
  const total = tasks.value.length
  const completed = tasks.value.filter(t => t.status === 'completed').length
  const processing = tasks.value.filter(t => t.status === 'processing').length
  const pending = total - completed - processing
  const totalVulns = tasks.value.reduce((sum, t) => sum + (t.vulnerabilities || 0), 0)

  return [
    { title: 'TOTAL TASKS', value: total, icon: '◉', class: 'stat-total' },
    { title: 'VULNERABILITIES', value: totalVulns, icon: '⚠', class: 'stat-vulns' },
    { title: 'COMPLETED', value: completed, icon: '✓', class: 'stat-completed' },
    { title: 'PENDING', value: pending, icon: '◯', class: 'stat-pending' }
  ]
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:8000/api/tasks/recent')
    tasks.value = Array.isArray(res.data) ? res.data : []
  } catch (error) {
    console.error('获取任务列表失败:', error)
    tasks.value = []
  } finally {
    loading.value = false
  }
}

const refreshTasks = () => {
  fetchTasks()
  ElMessage.success('数据已刷新')
}

const getLangClass = (lang) => {
  const map = {
    'Python': 'python',
    'JavaScript': 'js',
    'Java': 'java',
    'PHP': 'php',
    'Go': 'go',
    'Rust': 'rust',
    'Unknown': 'unknown'
  }
  return map[lang] || 'unknown'
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

const startAudit = async (task) => {
  try {
    await axios.post(`http://localhost:8000/api/tasks/${task.task_id}/start`)
    router.push({
      path: `/audit/${task.task_id}`,
      query: { file: task.filename, type: task.project_type }
    })
  } catch (error) {
    router.push({
      path: `/audit/${task.task_id}`,
      query: { file: task.filename, type: task.project_type }
    })
  }
}

const viewAudit = (task) => {
  router.push({
    path: `/audit/${task.task_id}`,
    query: { file: task.filename, type: task.project_type }
  })
}

const formatTime = (time) => {
  if (!time) return '--'
  return new Date(time).toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

onMounted(fetchTasks)
</script>

<style scoped>
.dashboard-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 20px;
}

.dashboard-header {
  margin-bottom: 40px;
  text-align: center;
}

.dashboard-header h1 {
  font-size: 32px;
  color: var(--primary);
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 8px;
}

.header-line {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  box-shadow: 0 0 10px var(--primary-glow);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 25px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  border-color: var(--primary);
  box-shadow: 0 0 20px var(--primary-glow);
}

.stat-icon {
  font-size: 40px;
  margin-right: 20px;
  opacity: 0.8;
}

.stat-total .stat-icon { color: var(--info); }
.stat-vulns .stat-icon { color: var(--danger); }
.stat-completed .stat-icon { color: var(--primary); }
.stat-pending .stat-icon { color: var(--text-secondary); }

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: var(--text);
  line-height: 1;
  margin-bottom: 5px;
}

.stat-title {
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 2px;
  text-transform: uppercase;
}

/* 任务区域 */
.tasks-section {
  padding: 25px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
}

.section-title {
  color: var(--primary);
  font-size: 18px;
  letter-spacing: 4px;
  margin: 0;
}

.refresh-btn {
  background: transparent;
  border: 1px solid var(--primary);
  color: var(--primary);
  padding: 8px 16px;
  font-family: inherit;
  font-size: 12px;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
}

.refresh-btn:hover {
  background: var(--primary);
  color: var(--bg-dark);
  box-shadow: 0 0 15px var(--primary-glow);
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  margin-bottom: 15px;
}

.empty-state p {
  margin-bottom: 20px;
  font-size: 16px;
  letter-spacing: 2px;
}

/* 任务表格 */
.tasks-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 0.8fr 1.2fr 1fr;
  gap: 15px;
  padding: 15px 20px;
  background: var(--bg-darker);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.task-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 0.8fr 1.2fr 1fr;
  gap: 15px;
  padding: 20px;
  background: var(--bg-darker);
  border: 1px solid var(--border-color);
  border-left: 4px solid var(--text-secondary);
  border-radius: 6px;
  align-items: center;
  transition: all 0.3s;
}

.task-row:hover {
  background: var(--bg-card);
  transform: translateX(5px);
}

.task-row.status-pending {
  border-left-color: var(--text-secondary);
}

.task-row.status-processing {
  border-left-color: var(--warning);
  box-shadow: 0 0 15px var(--warning-glow);
}

.task-row.status-completed {
  border-left-color: var(--primary);
}

/* 列样式 */
.col-file {
  min-width: 0;
}

.file-name {
  color: var(--text);
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-id {
  color: var(--text-muted);
  font-size: 11px;
  font-family: monospace;
}

/* 语言标签 */
.lang-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.lang-python {
  background: rgba(0, 204, 255, 0.15);
  color: #00ccff;
  border: 1px solid #00ccff;
}

.lang-js {
  background: rgba(255, 204, 0, 0.15);
  color: #ffcc00;
  border: 1px solid #ffcc00;
}

.lang-java {
  background: rgba(255, 0, 85, 0.15);
  color: #ff0055;
  border: 1px solid #ff0055;
}

.lang-php {
  background: rgba(136, 146, 250, 0.15);
  color: #8892fa;
  border: 1px solid #8892fa;
}

.lang-go {
  background: rgba(0, 255, 159, 0.15);
  color: var(--primary);
  border: 1px solid var(--primary);
}

.lang-rust {
  background: rgba(255, 170, 0, 0.15);
  color: #ffaa00;
  border: 1px solid #ffaa00;
}

.lang-unknown {
  background: rgba(160, 160, 160, 0.1);
  color: var(--text-muted);
  border: 1px solid var(--text-muted);
}

/* 状态标签 */
.status-badge {
  display: inline-block;
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  letter-spacing: 1px;
}

.status-badge.pending {
  background: rgba(160, 160, 160, 0.1);
  color: var(--text-secondary);
  border: 1px solid var(--text-secondary);
}

.status-badge.processing {
  background: rgba(255, 170, 0, 0.1);
  color: var(--warning);
  border: 1px solid var(--warning);
  animation: pulse-warning 2s infinite;
}

.status-badge.completed {
  background: rgba(0, 255, 159, 0.1);
  color: var(--primary);
  border: 1px solid var(--primary);
}

@keyframes pulse-warning {
  0%, 100% { box-shadow: 0 0 5px var(--warning-glow); }
  50% { box-shadow: 0 0 15px var(--warning-glow); }
}

/* 漏洞数 */
.vuln-count {
  font-size: 18px;
  font-weight: bold;
  color: var(--text-secondary);
}

.vuln-count.has-vuln {
  color: var(--danger);
  text-shadow: 0 0 10px var(--danger-glow);
}

.col-time {
  color: var(--text-secondary);
  font-size: 13px;
}

/* 操作按钮 */
.action-btn {
  padding: 8px 16px;
  border: none;
  font-family: inherit;
  font-size: 13px;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 4px;
  white-space: nowrap;
}

.action-btn.start {
  background: var(--primary);
  color: var(--bg-dark);
  font-weight: bold;
}

.action-btn.start:hover {
  box-shadow: 0 0 20px var(--primary-glow);
  transform: scale(1.05);
}

.action-btn.view {
  background: var(--warning);
  color: var(--bg-dark);
  font-weight: bold;
}

.action-btn.view:hover {
  box-shadow: 0 0 20px var(--warning-glow);
}

.action-btn.report {
  background: transparent;
  border: 2px solid var(--primary);
  color: var(--primary);
}

.action-btn.report:hover {
  background: var(--primary);
  color: var(--bg-dark);
}

.cyber-button {
  background: var(--primary);
  border: none;
  color: var(--bg-dark);
  padding: 12px 24px;
  font-family: inherit;
  font-size: 14px;
  font-weight: bold;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
  clip-path: polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%);
}

.cyber-button:hover {
  box-shadow: 0 0 20px var(--primary-glow);
  transform: translateY(-2px);
}

/* 响应式 */
@media (max-width: 1200px) {
  .table-header,
  .task-row {
    grid-template-columns: 1.5fr 0.8fr 0.8fr 0.6fr 1fr 0.9fr;
    gap: 10px;
    padding: 15px;
  }
}

@media (max-width: 900px) {
  .table-header,
  .task-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .table-header {
    display: none;
  }
  
  .task-row {
    position: relative;
    padding-left: 20px;
  }
  
  .col-action {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
  }
}
</style>