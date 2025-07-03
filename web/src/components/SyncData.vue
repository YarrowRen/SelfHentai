<template> 
  <div class="container">
    <button @click="startSync" :disabled="syncing">开始同步</button>
    <div class="terminal">
      <pre ref="terminalContent">{{ logs.join('\n') }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'

const logs = ref([])
const syncing = ref(false)
const terminalContent = ref(null)
const API = import.meta.env.VITE_API_BASE
const WS = import.meta.env.VITE_WS_BASE
let ws = null

async function connectWebSocket() {
  if (ws) return  // 防止重复连接
  // 建立 WebSocket 连接
  ws = new WebSocket(`${WS}/ws/logs`)
  
  ws.onmessage = (event) => {
    logs.value.push(event.data)
    nextTick(() => {
      const el = terminalContent.value
      el.scrollTop = el.scrollHeight
    })
  }

  ws.onerror = (error) => {
    logs.value.push("[ERROR] WebSocket 连接出错")
    stopSync()
  }

  ws.onclose = () => {
    logs.value.push("[INFO] WebSocket 连接关闭")
  }
}

async function startSync() {
  // 再次确认状态（防止状态不同步）
  const statusRes = await fetch(`${API}/api/gallery/sync/status`)
  const status = await statusRes.json()
  if (status.syncing) {
    logs.value.push("[INFO] 同步任务已在进行中，已连接日志流")
    syncing.value = true
    connectWebSocket()
    return
  }

  syncing.value = true
  logs.value = []
  connectWebSocket()

  try {
    const res = await fetch(`${API}/api/gallery/sync`, {
      method: "POST"
    })
    const data = await res.json()
    logs.value.push(`[INFO] 同步完成：共 ${data.count} 项`)
  } catch (err) {
    logs.value.push("[ERROR] 同步请求失败")
  } finally {
    stopSync()
  }
}

function stopSync() {
  syncing.value = false
  if (ws) {
    ws.close()
    ws = null
  }
}

onMounted(async () => {
  // 页面加载时检查是否在同步
  try {
    const res = await fetch(`${API}/api/gallery/sync/status`)
    const data = await res.json()
    if (data.syncing) {
      syncing.value = true
      logs.value.push("[INFO] 检测到同步正在进行，正在连接日志...")
      connectWebSocket()
    }
  } catch (err) {
    logs.value.push("[ERROR] 无法获取同步状态")
  }
})

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.container {
  padding: 1rem;
}

button {
  margin-bottom: 1rem;
  padding: 0.5rem 1rem;
  font-size: 16px;
}

.terminal {
  background: #111;
  color: #0f0;
  padding: 1rem;
  height: 650px;
  overflow-y: auto;
  font-family: monospace;
  border-radius: 8px;
  border: 1px solid #333;
}
</style>
