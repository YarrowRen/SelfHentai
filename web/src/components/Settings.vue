<template>
  <div class="settings-wrapper">
    <div class="settings-container">
      <h1 class="settings-title">Settings</h1>
      
      <!-- EX配置区域 -->
      <div class="config-section">
        <h2 class="section-title">
          ExHentai Configuration
        </h2>
        
        <div class="form-grid">
          <div class="form-group">
            <label for="exBase">Base URL</label>
            <select v-model="config.EXHENTAI_BASE_URL" id="exBase" class="form-select">
              <option value="https://exhentai.org/favorites.php">ExHentai</option>
              <option value="https://e-hentai.org/favorites.php">E-Hentai</option>
            </select>
          </div>

          <div class="form-group">
            <label for="igneous">Igneous</label>
            <input 
              v-model="config.EXHENTAI_COOKIE_IGNEOUS"
              id="igneous"
              type="text"
              class="form-input"
              placeholder="输入你的Igneous (可选)"
            />
          </div>

          <div class="form-group">
            <label for="memberId">Member ID</label>
            <input 
              v-model="config.EXHENTAI_COOKIE_MEMBER_ID"
              id="memberId"
              type="text"
              class="form-input"
              placeholder="输入你的Member ID"
            />
          </div>

          <div class="form-group">
            <label for="passHash">Pass Hash</label>
            <input 
              v-model="config.EXHENTAI_COOKIE_PASS_HASH"
              id="passHash"
              type="password"
              class="form-input"
              placeholder="输入你的Pass Hash"
            />
          </div>
        </div>
      </div>

      <!-- JM配置区域 -->
      <div class="config-section">
        <h2 class="section-title">
          JM Configuration
        </h2>
        
        <div class="form-grid">
          <div class="form-group">
            <label for="jmUsername">Username</label>
            <input 
              v-model="config.JM_USERNAME"
              id="jmUsername"
              type="text"
              class="form-input"
              placeholder="输入你的JM用户名"
            />
          </div>

          <div class="form-group">
            <label for="jmPassword">Password</label>
            <input 
              v-model="config.JM_PASSWORD"
              id="jmPassword"
              type="password"
              class="form-input"
              placeholder="输入你的JM密码"
            />
          </div>

          <div class="form-group full-width">
            <label for="jmVersion">App Version</label>
            <input 
              v-model="config.JM_APP_VERSION"
              id="jmVersion"
              type="text"
              class="form-input"
              placeholder="JM App版本号 (默认: 1.8.0)"
            />
          </div>

          <div class="form-group full-width">
            <label for="jmApiBases">API Base URLs</label>
            <textarea 
              v-model="apiBasesText"
              id="jmApiBases"
              class="form-textarea"
              rows="4"
              placeholder="输入API域名，每行一个"
            ></textarea>
            <small class="form-hint">每行输入一个API域名</small>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button 
          @click="loadConfig" 
          class="btn btn-secondary"
          :disabled="loading"
        >
          <span class="btn-icon">🔄</span>
          重新加载
        </button>
        
        <button 
          @click="saveConfig" 
          class="btn btn-primary"
          :disabled="loading || !hasChanges"
        >
          <span class="btn-icon">💾</span>
          {{ loading ? '保存中...' : '保存配置' }}
        </button>

        <button 
          @click="testConnection" 
          class="btn btn-test"
          :disabled="loading"
        >
          <span class="btn-icon">🔗</span>
          测试连接
        </button>
      </div>

      <!-- 状态消息 -->
      <div v-if="message" :class="['message', messageType]">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const API = import.meta.env.VITE_API_BASE

// 响应式数据
const config = ref({
  EXHENTAI_BASE_URL: 'https://exhentai.org/favorites.php',
  EXHENTAI_COOKIE_MEMBER_ID: '',
  EXHENTAI_COOKIE_PASS_HASH: '',
  EXHENTAI_COOKIE_IGNEOUS: '',
  JM_USERNAME: '',
  JM_PASSWORD: '',
  JM_APP_VERSION: '1.8.0',
  JM_API_BASES: []
})

const originalConfig = ref({})
const loading = ref(false)
const message = ref('')
const messageType = ref('info') // info, success, error

// API Base URLs 的文本表示
const apiBasesText = computed({
  get: () => config.value.JM_API_BASES.join('\n'),
  set: (value) => {
    config.value.JM_API_BASES = value.split('\n').filter(url => url.trim())
  }
})

// 检测是否有变更
const hasChanges = computed(() => {
  return JSON.stringify(config.value) !== JSON.stringify(originalConfig.value)
})

// 显示消息
const showMessage = (msg, type = 'info', duration = 3000) => {
  message.value = msg
  messageType.value = type
  if (duration > 0) {
    setTimeout(() => {
      message.value = ''
    }, duration)
  }
}

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API}/api/settings/config`)
    if (!response.ok) throw new Error('获取配置失败')
    
    const data = await response.json()
    config.value = { ...config.value, ...data }
    originalConfig.value = JSON.parse(JSON.stringify(config.value))
    showMessage('配置加载成功', 'success')
  } catch (error) {
    showMessage('加载配置失败: ' + error.message, 'error')
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API}/api/settings/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config.value)
    })
    
    if (!response.ok) throw new Error('保存配置失败')
    
    originalConfig.value = JSON.parse(JSON.stringify(config.value))
    showMessage('配置保存成功！请重启应用以生效', 'success', 5000)
  } catch (error) {
    showMessage('保存配置失败: ' + error.message, 'error')
  } finally {
    loading.value = false
  }
}

// 测试连接
const testConnection = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API}/api/settings/test-connection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config.value)
    })
    
    const result = await response.json()
    
    if (response.ok) {
      showMessage(result.message || '连接测试成功', 'success')
    } else {
      showMessage(result.error || '连接测试失败', 'error')
    }
  } catch (error) {
    showMessage('测试连接失败: ' + error.message, 'error')
  } finally {
    loading.value = false
  }
}

// 页面加载时获取配置
onMounted(() => {
  loadConfig()
})
</script>

<style src="../assets/Settings.css"></style>