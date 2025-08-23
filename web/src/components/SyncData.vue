<template> 
  <div class="container">
    <div class="sync-controls">
      <div class="provider-selection">
        <label>
          <input type="radio" v-model="selectedProvider" value="ex" />
          <span>EX 数据同步</span>
        </label>
        <label>
          <input type="radio" v-model="selectedProvider" value="jm" />
          <span>JM 数据同步</span>
        </label>
      </div>
      <button @click="startSync" :disabled="syncing">
        开始{{ selectedProvider === 'ex' ? 'EX' : 'JM' }}同步
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
const selectedProvider = ref('ex')
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
    const res = await fetch(`${API}/api/gallery/sync?provider=${selectedProvider.value}`, {
      method: "POST"
    })
    const data = await res.json()
    logs.value.push(`[INFO] ${selectedProvider.value.toUpperCase()} 同步完成：共 ${data.count} 项`)
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
  background: var(--bg-color);
  color: var(--text-color);
  transition: all 0.3s ease;
}

.sync-controls {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.provider-selection {
  display: flex;
  gap: 1rem;
}

.provider-selection label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--surface-color);
  color: var(--text-color);
  transition: all 0.3s ease;
  font-weight: 500;
}

.provider-selection label:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  transform: translateY(-1px);
}

.provider-selection input[type="radio"]:checked + span {
  color: var(--primary-color);
  font-weight: 600;
}

.provider-selection input[type="radio"] {
  margin: 0;
  accent-color: var(--primary-color);
}

button {
  padding: 0.75rem 1.5rem;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-hover) 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(100, 108, 255, 0.25);
}

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(100, 108, 255, 0.4);
  background: linear-gradient(135deg, var(--primary-color-hover) 0%, var(--primary-color) 100%);
}

button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(100, 108, 255, 0.3);
}

button:disabled {
  background: var(--border-color);
  color: var(--text-color);
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.terminal {
  background: var(--surface-color);
  color: var(--text-color);
  padding: 1.5rem;
  height: 650px;
  overflow-y: auto;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  border-radius: 12px;
  border: 2px solid var(--border-color);
  box-shadow: 0 4px 12px var(--shadow-color);
  position: relative;
  transition: all 0.3s ease;
}

.terminal::before {
  content: '● ● ●';
  position: absolute;
  top: 10px;
  left: 15px;
  color: var(--text-color);
  opacity: 0.5;
  font-size: 12px;
}

.terminal pre {
  margin-top: 25px;
  line-height: 1.4;
  font-size: 14px;
}

/* 浅色模式下的终端特殊样式 */
:global(.my-app-light) .terminal {
  background: #2d3748;
  color: #e2e8f0;
  border-color: #4a5568;
}

/* 深色模式下保持绿色终端文字 */
:global(.my-app-dark) .terminal {
  color: #00ff00;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sync-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .provider-selection {
    justify-content: center;
  }
  
  .terminal {
    height: 500px;
    padding: 1rem;
  }
}
</style>
