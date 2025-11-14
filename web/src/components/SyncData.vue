<template> 
  <div class="container">
    <div class="sync-controls">
      <h2>ExHentai 数据同步</h2>
      <button @click="startSync" :disabled="syncing">
        {{ syncing ? '同步中...' : '开始EX同步' }}
      </button>
    </div>
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
// 移除了JM相关功能，固定使用ExHentai提供商
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
    const res = await fetch(`${API}/api/gallery/sync?provider=ex`, {
      method: "POST"
    })
    const data = await res.json()
    logs.value.push(`[INFO] ExHentai 同步完成：共 ${data.count} 项`)
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

<style src="../assets/SyncData.css"></style>
