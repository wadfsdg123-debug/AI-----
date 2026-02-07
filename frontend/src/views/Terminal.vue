<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

// ✅ 新包名（只改这3行）
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const router = useRouter()
const terminalRef = ref(null)
const connected = ref(false)

let term = null
let fitAddon = null
let ws = null

// 初始化终端
const initTerminal = () => {
  term = new Terminal({
    rows: 30,
    cols: 100,
    fontSize: 14,
    cursorBlink: true,
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4'
    }
  })
  
  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(terminalRef.value)
  fitAddon.fit()
  
  term.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data)
    }
  })
}

// 连接 WebSocket
const connect = () => {
  ws = new WebSocket('ws://localhost:8080/ssh')
  
  ws.onopen = () => {
    connected.value = true
    term.writeln('\r\n\x1b[32m[系统] WebSocket 连接成功\x1b[0m\r\n')
  }
  
  ws.onmessage = (event) => {
    term.write(event.data)
  }
  
  ws.onclose = () => {
    connected.value = false
    term.writeln('\r\n\x1b[31m[系统] 连接已断开\x1b[0m')
  }
  
  ws.onerror = () => {
    term.writeln('\r\n\x1b[31m[系统] 连接错误\x1b[0m')
  }
}

const disconnect = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

const back = () => {
  disconnect()
  router.push('/')
}

onMounted(() => {
  initTerminal()
})

onUnmounted(() => {
  disconnect()
  if (term) {
    term.dispose()
  }
})
</script>

<template>
  <div class="terminal-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>WebSSH 终端</span>
          <div>
            <el-button type="primary" size="small" @click="connect" :disabled="connected">
              {{ connected ? '已连接' : '连接' }}
            </el-button>
            <el-button size="small" @click="back">返回首页</el-button>
          </div>
        </div>
      </template>
      <div ref="terminalRef" class="terminal-wrapper"></div>
    </el-card>
  </div>
</template>

<style scoped>
.terminal-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.terminal-wrapper {
  background: #1e1e1e;
  border-radius: 4px;
  padding: 10px;
  height: 500px;
  overflow: hidden;
}
:deep(.xterm) {
  height: 100%;
}
</style>