<template>
  <div class="audit-page">
    <!-- 头部 -->
    <div class="audit-header">
      <h1 class="glitch" data-text="SECURITY AUDIT">SECURITY AUDIT</h1>
      <div class="task-meta">
        <span class="meta-item">FILE: {{ filename }}</span>
        <span class="meta-item">TYPE: {{ projectType }}</span>
        <span class="meta-item">ID: {{ taskId }}</span>
      </div>
    </div>

    <!-- 连接状态 -->
    <div class="cyber-card status-bar" :class="{ 'connected': wsConnected }">
      <span class="status-indicator"></span>
      <span class="status-text">{{ wsConnected ? 'SYSTEM ONLINE' : 'CONNECTING...' }}</span>
    </div>

    <!-- 进度条 -->
    <div class="cyber-card progress-section">
      <div class="progress-header">
        <span class="progress-label">AUDIT PROGRESS</span>
        <span class="progress-value">{{ progress }}%</span>
      </div>
      <div class="cyber-progress">
        <div class="cyber-progress-fill" :style="{ width: progress + '%' }">
          <div class="progress-glow"></div>
        </div>
      </div>
      <div class="status-message">{{ statusMsg }}</div>
    </div>

    <!-- 终端日志 -->
    <div class="cyber-card terminal-section">
      <div class="terminal-header">
        <div class="terminal-title-wrapper">
          <span class="terminal-prompt">>></span>
          <span class="terminal-title">TERMINAL_OUTPUT</span>
        </div>
        <div class="terminal-controls">
          <span class="control-btn minimize">_</span>
          <span class="control-btn maximize">□</span>
          <span class="control-btn close">×</span>
        </div>
      </div>
      <div class="terminal-body" ref="terminalBody">
        <div 
          v-for="(log, i) in logs" 
          :key="i" 
          class="terminal-line"
          :class="'level-' + log.level"
        >
          <span class="line-time">[{{ log.time }}]</span>
          <span class="line-content">{{ log.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="terminal-empty">
          > 等待连接...
        </div>
        <div class="terminal-cursor">_</div>
      </div>
    </div>

    <!-- 漏洞列表 -->
    <div v-if="vulns.length > 0" class="vulnerabilities-section">
      <h2 class="section-title glitch" data-text="THREATS DETECTED">
        THREATS DETECTED [{{ vulns.length }}]
      </h2>
      
      <div v-for="v in vulns" :key="v.id" class="cyber-card vuln-card" :class="'severity-' + v.severity">
        <div class="vuln-header">
          <div class="vuln-icon">⚠</div>
          <div class="vuln-title">
            <span class="vuln-type">{{ v.type }}</span>
            <span class="vuln-location">{{ v.file }}:{{ v.line }}</span>
          </div>
          <div class="vuln-badge" :class="v.severity">{{ v.severity }}</div>
        </div>
        
        <div class="vuln-body">
          <div class="vuln-section">
            <h4>DESCRIPTION</h4>
            <p>{{ v.description }}</p>
          </div>
          
          <div class="vuln-section">
            <h4>SUGGESTION</h4>
            <p>{{ v.suggestion }}</p>
          </div>
          
          <div v-if="v.codeSnippet" class="vuln-section">
            <h4>CODE SNIPPET</h4>
            <pre class="code-block"><code>{{ v.codeSnippet }}</code></pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 完成操作 -->
    <div v-if="completed" class="cyber-card action-section">
      <div class="success-message">✓ AUDIT COMPLETED</div>
      <div class="action-buttons">
        <button class="cyber-button" @click="downloadReport">
          [ DOWNLOAD REPORT ]
        </button>
        <button class="cyber-button cyber-button-secondary" @click="goBack">
          [ RETURN TO DASHBOARD ]
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVulnTemplate } from '../utils/vulnTemplates.js'
import { generateMarkdownReport, downloadReport as downloadReportFile } from '../utils/reportGenerator.js'

const route = useRoute()
const router = useRouter()

const taskId = ref(route.params.id)
const filename = ref(route.query.file || 'UNKNOWN')
const projectType = ref(route.query.type || 'UNKNOWN')

const wsConnected = ref(false)
const progress = ref(0)
const statusMsg = ref('INITIALIZING...')
const logs = ref([])
const vulns = ref([])
const completed = ref(false)

const terminalBody = ref(null)
let ws = null

const addLog = (message, level = 'info') => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false })
  logs.value.push({ time, message, level })
  if (logs.value.length > 200) logs.value.shift()
  
  nextTick(() => {
    if (terminalBody.value) {
      terminalBody.value.scrollTop = terminalBody.value.scrollHeight
    }
  })
}

const connectWS = () => {
  const url = `ws://localhost:8000/ws/audit/${taskId.value}`
  addLog('Connecting to audit server...', 'info')
  
  ws = new WebSocket(url)
  
  ws.onopen = () => {
    wsConnected.value = true
    addLog('Connection established', 'success')
  }
  
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      handleMessage(msg)
    } catch (e) {
      addLog('Parse error: ' + e.message, 'error')
    }
  }
  
  ws.onerror = () => {
    wsConnected.value = false
    addLog('Connection error', 'error')
  }
  
  ws.onclose = () => {
    wsConnected.value = false
    addLog('Connection closed', 'warning')
  }
}

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
      const template = getVulnTemplate(msg.data?.type)
      const vuln = {
        id: Date.now() + Math.random(),
        ...template,
        ...msg.data
      }
      vulns.value.push(vuln)
      addLog(`ALERT: ${vuln.type} detected in ${vuln.file}`, 'error')
      break
      
    case 'completed':
      completed.value = true
      addLog('AUDIT COMPLETED SUCCESSFULLY', 'success')
      ElMessage.success('审计完成')
      break
      
    case 'error':
      addLog('ERROR: ' + (msg.data?.message || 'Unknown error'), 'error')
      break
  }
}

const downloadReport = () => {
  const task = {
    taskId: taskId.value,
    filename: filename.value,
    projectType: projectType.value,
    status: 'completed'
  }
  const markdown = generateMarkdownReport(task, vulns.value)
  downloadReportFile(markdown, `AUDIT_REPORT_${taskId.value}.md`)
}

const goBack = () => {
  router.push('/dashboard')
}

onMounted(() => {
  if (!taskId.value) {
    ElMessage.error('Missing task ID')
    return
  }
  connectWS()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.audit-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}

.audit-header {
  margin-bottom: 30px;
  text-align: center;
}

.audit-header h1 {
  font-size: 36px;
  color: var(--primary);
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 8px;
}

.task-meta {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.meta-item {
  background: var(--bg-card);
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  margin-bottom: 20px;
  border-left: 4px solid var(--danger);
  transition: all 0.3s;
}

.status-bar.connected {
  border-left-color: var(--primary);
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--danger);
  animation: blink 1s infinite;
  box-shadow: 0 0 10px var(--danger-glow);
  flex-shrink: 0;
}

.status-bar.connected .status-indicator {
  background: var(--primary);
  box-shadow: 0 0 10px var(--primary-glow);
  animation: none;
}

.status-text {
  color: var(--text-secondary);
  font-size: 14px;
  letter-spacing: 2px;
}

/* 进度区域 */
.progress-section {
  padding: 25px;
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.progress-label {
  color: var(--text-secondary);
  font-size: 14px;
  letter-spacing: 2px;
}

.progress-value {
  color: var(--primary);
  font-size: 24px;
  font-weight: bold;
  text-shadow: 0 0 10px var(--primary-glow);
}

.cyber-progress {
  height: 30px;
  background: var(--bg-darker);
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
}

.cyber-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--info));
  position: relative;
  transition: width 0.3s ease;
}

.progress-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 30px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-30px); }
  100% { transform: translateX(30px); }
}

.status-message {
  margin-top: 15px;
  color: var(--text-secondary);
  font-size: 14px;
  text-align: center;
}

/* 终端区域 - 关键修复 */
.terminal-section {
  margin-bottom: 20px;
  overflow: hidden;
}

.terminal-header {
  background: var(--bg-darker);
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  min-height: 45px;
}

/* 关键：标题包装器，确保内容完整显示 */
.terminal-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0; /* 允许flex子项收缩 */
}

.terminal-prompt {
  color: var(--primary);
  font-size: 14px;
  font-weight: bold;
  flex-shrink: 0;
}

.terminal-title {
  color: var(--primary);
  font-size: 14px;
  letter-spacing: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.terminal-controls {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  margin-left: 15px;
}

.control-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.2s;
}

.control-btn:hover {
  color: var(--text);
  background: rgba(255,255,255,0.1);
}

.terminal-body {
  background: #0a0a0f;
  padding: 20px;
  height: 400px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
}

.terminal-line {
  display: flex;
  gap: 10px;
  margin: 2px 0;
}

.line-time {
  color: #444;
  min-width: 80px;
  flex-shrink: 0;
}

.line-content {
  color: #0f0;
  flex: 1;
  word-break: break-all;
}

.level-warning .line-content { color: #fa0; }
.level-error .line-content { color: #f05; }
.level-success .line-content { color: #0f0; }
.level-info .line-content { color: #0cf; }

.terminal-empty {
  color: #444;
  font-style: italic;
}

.terminal-cursor {
  color: #0f0;
  animation: cursor-blink 0.8s infinite;
  display: inline-block;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 漏洞区域 */
.vulnerabilities-section {
  margin-bottom: 20px;
}

.section-title {
  color: var(--danger);
  font-size: 24px;
  margin-bottom: 20px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 4px;
}

.vuln-card {
  margin-bottom: 20px;
  border-left: 4px solid var(--warning);
}

.vuln-card.severity-critical {
  border-left-color: var(--danger);
  box-shadow: 0 0 20px var(--danger-glow);
}

.vuln-card.severity-high {
  border-left-color: var(--danger);
}

.vuln-card.severity-medium {
  border-left-color: var(--warning);
}

.vuln-card.severity-low {
  border-left-color: var(--info);
}

.vuln-header {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: var(--bg-darker);
  border-bottom: 1px solid var(--border-color);
}

.vuln-icon {
  font-size: 24px;
  color: var(--danger);
  flex-shrink: 0;
}

.vuln-title {
  flex: 1;
  min-width: 0;
}

.vuln-type {
  display: block;
  color: var(--text);
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
}

.vuln-location {
  color: var(--text-muted);
  font-size: 12px;
  font-family: monospace;
}

.vuln-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.vuln-badge.critical {
  background: var(--danger);
  color: #fff;
  box-shadow: 0 0 10px var(--danger-glow);
}

.vuln-badge.high {
  background: rgba(255, 0, 85, 0.2);
  color: var(--danger);
  border: 1px solid var(--danger);
}

.vuln-badge.medium {
  background: rgba(255, 170, 0, 0.2);
  color: var(--warning);
  border: 1px solid var(--warning);
}

.vuln-badge.low {
  background: rgba(0, 204, 255, 0.2);
  color: var(--info);
  border: 1px solid var(--info);
}

.vuln-body {
  padding: 20px;
}

.vuln-section {
  margin-bottom: 20px;
}

.vuln-section:last-child {
  margin-bottom: 0;
}

.vuln-section h4 {
  color: var(--primary);
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.vuln-section p {
  color: var(--text-secondary);
  line-height: 1.8;
}

.code-block {
  background: #0a0a0f;
  border: 1px solid var(--border-color);
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Consolas', monospace;
  font-size: 13px;
  color: #0f0;
  line-height: 1.6;
}

/* 操作区域 */
.action-section {
  padding: 40px;
  text-align: center;
}

.success-message {
  color: var(--primary);
  font-size: 28px;
  margin-bottom: 30px;
  text-transform: uppercase;
  letter-spacing: 4px;
  text-shadow: 0 0 20px var(--primary-glow);
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.cyber-button {
  background: transparent;
  border: 2px solid var(--primary);
  color: var(--primary);
  padding: 15px 30px;
  font-family: inherit;
  font-size: 14px;
  letter-spacing: 2px;
  text-transform: uppercase;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  clip-path: polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%);
}

.cyber-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--primary);
  transition: left 0.3s;
  z-index: -1;
}

.cyber-button:hover {
  color: var(--bg-dark);
}

.cyber-button:hover::before {
  left: 0;
}

.cyber-button-secondary {
  border-color: var(--text-secondary);
  color: var(--text-secondary);
}

.cyber-button-secondary::before {
  background: var(--text-secondary);
}
</style>