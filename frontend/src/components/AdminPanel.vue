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
