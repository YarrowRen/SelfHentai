<template>
  <div class="container">
    <button @click="startSync" :disabled="syncing">开始同步</button>
    <div class="terminal">
      <pre ref="terminalContent">{{ logs.join('\n') }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, nextTick } from 'vue'

const logs = ref([])
const syncing = ref(false)
const terminalContent = ref(null)

let ws = null

async function startSync() {
  syncing.value = true
  logs.value = []

  // 建立 WebSocket 连接
  ws = new WebSocket("ws://localhost:5001/ws/logs")
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
    logs.value.push("[INFO] WebSocket 连接已关闭")
  }

  // 等待连接成功后调用同步 API
  ws.onopen = async () => {
    // logs.value.push("[INFO] 开始同步任务...")
    try {
      const res = await fetch("http://localhost:5001/api/gallery/sync", {
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
}

function stopSync() {
  syncing.value = false
  if (ws) {
    ws.close()
    ws = null
  }
}

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
