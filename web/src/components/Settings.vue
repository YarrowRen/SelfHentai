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


      <!-- AI翻译配置区域 -->
      <div class="config-section">
        <h2 class="section-title">
          AI Translation Configuration
        </h2>
        
        <div class="form-grid">
          <div class="form-group">
            <label for="translationProvider">LLM Provider</label>
            <select v-model="config.TRANSLATION_PROVIDER" id="translationProvider" class="form-select" @change="onProviderChange">
              <option value="volcano">火山引擎 (豆包)</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="qwen">阿里千问 (Qwen)</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>

          <div class="form-group">
            <label for="translationBaseUrl">API Base URL</label>
            <input 
              v-model="config.TRANSLATION_BASE_URL"
              id="translationBaseUrl"
              type="text"
              class="form-input"
              placeholder="API 基础地址"
            />
          </div>

          <div class="form-group">
            <label for="translationModel">Model Name</label>
            <input 
              v-model="config.TRANSLATION_MODEL"
              id="translationModel"
              type="text"
              class="form-input"
              placeholder="模型名称"
            />
          </div>

          <div class="form-group">
            <label for="translationApiKeyEnv">API Key Variable</label>
            <input 
              v-model="config.TRANSLATION_API_KEY_ENV"
              id="translationApiKeyEnv"
              type="text"
              class="form-input"
              placeholder="环境变量名"
              readonly
            />
          </div>

          <div class="form-group full-width">
            <label :for="`apiKey-${config.TRANSLATION_PROVIDER}`">{{ getApiKeyLabel() }}</label>
            <input 
              :value="getApiKeyValue()"
              @input="setApiKeyValue($event.target.value)"
              :id="`apiKey-${config.TRANSLATION_PROVIDER}`"
              type="password"
              class="form-input"
              :placeholder="`输入你的 ${getProviderName()} API Key`"
            />
          </div>
        </div>

        <div class="provider-info">
          <h4>{{ getProviderName() }} 配置说明</h4>
          <div v-html="getProviderDescription()"></div>
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
  // AI翻译配置
  TRANSLATION_PROVIDER: 'volcano',
  TRANSLATION_BASE_URL: 'https://ark.cn-beijing.volces.com/api/v3',
  TRANSLATION_MODEL: 'doubao-1-5-lite-32k-250115',
  TRANSLATION_API_KEY_ENV: 'ARK_API_KEY',
  ARK_API_KEY: '',
  OPENAI_API_KEY: '',
  ANTHROPIC_API_KEY: '',
  DASHSCOPE_API_KEY: '',
  GEMINI_API_KEY: ''
})

const originalConfig = ref({})
const loading = ref(false)
const message = ref('')
const messageType = ref('info') // info, success, error


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

// 翻译服务商配置映射
const providerConfigs = {
  volcano: {
    name: '火山引擎 (豆包)',
    baseUrl: 'https://ark.cn-beijing.volces.com/api/v3',
    model: 'doubao-1-5-lite-32k-250115',
    apiKeyEnv: 'ARK_API_KEY',
    description: `
      <p><strong>火山引擎豆包模型</strong>：字节跳动出品的大语言模型</p>
      <ul>
        <li>获取API Key：<a href="https://console.volcengine.com/ark" target="_blank">火山引擎控制台</a></li>
      </ul>
    `
  },
  openai: {
    name: 'OpenAI (GPT)',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    apiKeyEnv: 'OPENAI_API_KEY',
    description: `
      <p><strong>OpenAI GPT模型</strong>：业界领先的大语言模型，翻译质量极高</p>
      <ul>
        <li>获取API Key：<a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a></li>
      </ul>
    `
  },
  anthropic: {
    name: 'Anthropic (Claude)',
    baseUrl: 'https://api.anthropic.com/v1',
    model: 'claude-3-5-haiku-20241022',
    apiKeyEnv: 'ANTHROPIC_API_KEY',
    description: `
      <p><strong>Anthropic Claude模型</strong>：注重安全性和可靠性的大语言模型</p>
      <ul>
        <li>获取API Key：<a href="https://console.anthropic.com/" target="_blank">Anthropic Console</a></li>
      </ul>
    `
  },
  qwen: {
    name: '阿里千问 (Qwen)',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus',
    apiKeyEnv: 'DASHSCOPE_API_KEY',
    description: `
      <p><strong>阿里千问模型</strong>：阿里巴巴出品的中文优化大语言模型</p>
      <ul>
        <li>获取API Key：<a href="https://dashscope.console.aliyun.com/apiKey" target="_blank">DashScope控制台</a></li>
      </ul>
    `
  },
  gemini: {
    name: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    model: 'gemini-1.5-flash',
    apiKeyEnv: 'GEMINI_API_KEY',
    description: `
      <p><strong>Google Gemini模型</strong>：Google出品的多模态大语言模型</p>
      <ul>
        <li>获取API Key：<a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
      </ul>
    `
  }
}

// 翻译配置相关方法
const getProviderName = () => {
  return providerConfigs[config.value.TRANSLATION_PROVIDER]?.name || '未知服务商'
}

const getProviderDescription = () => {
  return providerConfigs[config.value.TRANSLATION_PROVIDER]?.description || ''
}

const getApiKeyLabel = () => {
  return `${getProviderName()} API Key`
}

const getApiKeyValue = () => {
  const keyEnv = config.value.TRANSLATION_API_KEY_ENV
  return config.value[keyEnv] || ''
}

const setApiKeyValue = (value) => {
  const keyEnv = config.value.TRANSLATION_API_KEY_ENV
  config.value[keyEnv] = value
}

// 切换服务商时更新配置
const onProviderChange = () => {
  const providerConfig = providerConfigs[config.value.TRANSLATION_PROVIDER]
  if (providerConfig) {
    config.value.TRANSLATION_BASE_URL = providerConfig.baseUrl
    config.value.TRANSLATION_MODEL = providerConfig.model
    config.value.TRANSLATION_API_KEY_ENV = providerConfig.apiKeyEnv
  }
}

// 页面加载时获取配置
onMounted(() => {
  loadConfig()
})
</script>

<style src="../assets/Settings.css"></style>