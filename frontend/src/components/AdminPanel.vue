<template>
  <div class="admin-container">
    <h1>数据管理</h1>
    
    <div class="admin-card">
      <h2>缓存状态</h2>
      <div class="status-info" v-if="cacheInfo">
        <p><span class="label">缓存文件：</span>{{ cacheInfo.cache_file }}</p>
        <p><span class="label">缓存时间：</span>{{ cacheInfo.cache_time }}</p>
        <p><span class="label">状态：</span>
          <span :class="['status-badge', cacheInfo.is_valid ? 'valid' : 'invalid']">
            {{ cacheInfo.is_valid ? '有效' : '已过期' }}
          </span>
        </p>
        <p><span class="label">过期时间：</span>{{ cacheInfo.expires_in }}</p>
        <p><span class="label">文件大小：</span>{{ formatFileSize(cacheInfo.file_size) }}</p>
      </div>
      <p v-else>加载中...</p>
    </div>

    <div class="admin-card">
      <h2>操作</h2>
      <div class="action-buttons">
        <button @click="refreshCache" :disabled="loading" class="btn btn-primary">
          {{ loading ? '刷新中...' : '刷新缓存' }}
        </button>
        <button @click="clearCache" :disabled="loading" class="btn btn-danger">
          清除缓存
        </button>
        <button @click="goHome" class="btn btn-secondary">
          返回首页
        </button>
      </div>
    </div>

    <div class="message" v-if="message" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { refreshCache, getCacheInfo, clearCache as deleteCache } from '../api/stats'

const router = useRouter()
const cacheInfo = ref(null)
const loading = ref(false)
const message = ref('')
const messageType = ref('success')

const loadCacheInfo = async () => {
  try {
    const res = await getCacheInfo()
    cacheInfo.value = res.data.data
  } catch (error) {
    console.error('获取缓存信息失败', error)
    message.value = '获取缓存信息失败：' + error.message
    messageType.value = 'error'
  }
}

const refreshCacheHandler = async () => {
  loading.value = true
  message.value = ''
  try {
    const res = await refreshCache(true)
    message.value = res.data.message || '缓存刷新成功'
    messageType.value = 'success'
    await loadCacheInfo()
  } catch (error) {
    console.error('刷新缓存失败', error)
    message.value = '刷新缓存失败：' + error.message
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const clearCacheHandler = async () => {
  if (!confirm('确定要清除缓存吗？')) return
  
  loading.value = true
  message.value = ''
  try {
    const res = await deleteCache()
    message.value = res.data.message || '缓存已清除'
    messageType.value = 'success'
    await loadCacheInfo()
  } catch (error) {
    console.error('清除缓存失败', error)
    message.value = '清除缓存失败：' + error.message
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const goHome = () => {
  router.push('/')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  loadCacheInfo()
})
</script>

<style scoped>
.admin-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.admin-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.admin-card h2 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 8px;
}

.status-info p {
  margin: 12px 0;
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
}

.label {
  font-weight: 600;
  color: #666;
  min-width: 80px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-badge.valid {
  background: #e6f7e6;
  color: #52c41a;
}

.status-badge.invalid {
  background: #fff1f0;
  color: #ff4d4f;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-danger {
  background: #ff4d4f;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #ff7875;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background: #d9d9d9;
}

.message {
  padding: 12px 20px;
  border-radius: 8px;
  margin-top: 20px;
  text-align: center;
}

.message.success {
  background: #e6f7e6;
  color: #52c41a;
}

.message.error {
  background: #fff1f0;
  color: #ff4d4f;
}

@media (max-width: 768px) {
  .admin-container {
    padding: 12px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
