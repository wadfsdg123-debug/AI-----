<template>
  <div class="audit-page">
    <h2>🔍 代码审计 - {{ taskId }}</h2>
    
    <!-- 连接状态 -->
    <el-alert :type="wsConnected ? 'success' : 'error'" :closable="false">
      WebSocket: {{ wsConnected ? '已连接' : '未连接' }}
    </el-alert>

    <!-- 进度条 -->
    <div class="section">
      <h3>进度: {{ progress }}%</h3>
      <el-progress :percentage="progress" :status="progressStatus" />
      <p>{{ statusMsg }}</p>
    </div>

    <!-- 终端日志 -->
    <div class="section">
      <h3>🖥️ 实时日志</h3>
      <div class="terminal-box">
        <div v-for="(log, i) in logs" :key="i" :class="'log-' + log.level">
          [{{ log.time }}] {{ log.message }}
        </div>
      </div>
    </div>

    <!-- 漏洞列表 -->
    <div class="section" v-if="vulns.length > 0">
      <h3>🐛 发现的漏洞 ({{ vulns.length }})</h3>
      <el-card v-for="v in vulns" :key="v.id" class="vuln-card">
        <el-tag :type="getSeverityType(v.severity)">{{ v.severity }}</el-tag>
        <strong>{{ v.type }}</strong>
        <p>{{ v.file }}:{{ v.line }}</p>
        <p>{{ v.description }}</p>
      </el-card>
    </div>

    <!-- 下载按钮 -->
    <div class="section" v-if="completed">
      <el-button type="primary" @click="downloadReport">下载报告</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const taskId = ref(route.params.id)

// 状态
const wsConnected = ref(false)
const progress = ref(0)
const progressStatus = ref('')
const statusMsg = ref('准备开始...')
const logs = ref([])
const vulns = ref([])
const completed = ref(false)

let ws = null

// 添加日志
const addLog = (message, level = 'info') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ time, message, level })
  // 限制日志数量
  if (logs.value.length > 100) logs.value.shift()
}

// WebSocket 连接
const connectWS = () => {
  const url = `ws://localhost:8000/ws/audit/${taskId.value}`
  console.log('连接 WebSocket:', url)
  
  ws = new WebSocket(url)
  
  ws.onopen = () => {
    console.log('WebSocket 已连接')
    wsConnected.value = true
    addLog('WebSocket 连接成功', 'success')
  }
  
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      console.log('收到消息:', msg.type, msg)
      
      handleMessage(msg)
    } catch (e) {
      console.error('消息解析失败:', e)
      addLog('消息解析错误: ' + e.message, 'error')
    }
  }
  
  ws.onerror = (e) => {
    console.error('WebSocket 错误:', e)
    wsConnected.value = false
    addLog('WebSocket 错误', 'error')
  }
  
  ws.onclose = () => {
    console.log('WebSocket 关闭')
    wsConnected.value = false
    addLog('WebSocket 连接关闭', 'warning')
  }
}

// 处理消息
const handleMessage = (msg) => {
  switch (msg.type) {
    case 'status_update':
      progress.value = msg.data?.progress || 0
      statusMsg.value = msg.data?.message || ''
      addLog(`[${progress.value}%] ${statusMsg.value}`, 'info')
      break
      
    case 'log':
      addLog(msg.data?.message || '', msg.data?.level || 'info')
      break
      
    case 'vuln_found':
      const vuln = {
        id: Date.now() + Math.random(),
        ...msg.data
      }
      vulns.value.push(vuln)
      addLog(`发现漏洞: ${vuln.type}`, 'error')
      break
      
    case 'completed':
      completed.value = true
      progressStatus.value = 'success'
      addLog('✅ 审计完成！', 'success')
      ElMessage.success('审计完成')
      break
      
    case 'error':
      progressStatus.value = 'exception'
      addLog('错误: ' + (msg.data?.message || '未知错误'), 'error')
      break
      
    default:
      console.log('未知消息类型:', msg.type)
  }
}

// 下载报告
const downloadReport = () => {
  window.open(`http://localhost:8000/api/report/${taskId.value}/markdown`)
}

// 获取严重程度样式
const getSeverityType = (severity) => {
  const map = {
    'critical': 'danger',
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return map[severity] || 'info'
}

onMounted(() => {
  console.log('AuditView 挂载, taskId:', taskId.value)
  if (!taskId.value) {
    ElMessage.error('缺少任务ID')
    return
  }
  connectWS()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.audit-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.section {
  margin: 20px 0;
}
.terminal-box {
  background: #1a1a1a;
  color: #0f0;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  max-height: 400px;
  overflow-y: auto;
}
.log-info { color: #0f0; }
.log-success { color: #0f0; }
.log-warning { color: #ff0; }
.log-error { color: #f00; }
.vuln-card {
  margin: 10px 0;
}
</style>