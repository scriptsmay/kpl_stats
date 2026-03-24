<template>
  <div class="admin-container">
    <h1>数据管理</h1>

    <!-- 缓存状态概览 -->
    <div class="admin-card">
      <h2>缓存状态概览</h2>
      <div class="cache-overview" v-if="allCacheInfo">
        <div class="cache-status-item" v-for="type in seasonTypes" :key="type">
          <div class="cache-status-header">
            <span class="cache-type-label">{{ getTypeLabel(type) }}</span>
            <span 
              :class="['status-badge', getCacheStatus(type).valid ? 'valid' : 'invalid']"
            >
              {{ getCacheStatus(type).valid ? '有效' : '已过期' }}
            </span>
          </div>
          <div class="cache-status-details" v-if="allCacheInfo[type].exists">
            <p><span class="label">缓存时间：</span>{{ formatTime(allCacheInfo[type].cache_time) }}</p>
            <p><span class="label">过期时间：</span>{{ allCacheInfo[type].expires_in }}</p>
            <p><span class="label">文件大小：</span>{{ formatFileSize(allCacheInfo[type].file_size) }}</p>
          </div>
          <div class="cache-status-empty" v-else>
            <p>暂无缓存</p>
          </div>
        </div>
      </div>
      <p v-else>加载中...</p>
    </div>

    <!-- 批量操作 -->
    <div class="admin-card">
      <h2>批量操作</h2>
      <div class="action-buttons">
        <button @click="refreshAll" :disabled="loading" class="btn btn-primary">
          {{ loading ? '刷新中...' : '刷新全部缓存' }}
        </button>
        <button @click="clearAll" :disabled="loading" class="btn btn-danger">
          清除所有缓存
        </button>
      </div>
    </div>

    <!-- 单个缓存操作 -->
    <div class="admin-card">
      <h2>单个缓存操作</h2>
      <div class="single-cache-actions">
        <div class="single-cache-action" v-for="type in seasonTypes" :key="type">
          <span class="cache-type-label">{{ getTypeLabel(type) }}</span>
          <div class="action-buttons">
            <button @click="refreshCache(type)" :disabled="loading" class="btn btn-primary btn-sm">
              刷新
            </button>
            <button @click="clearCache(type)" :disabled="loading" class="btn btn-danger btn-sm">
              清除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 存档信息 -->
    <div class="admin-card">
      <h2>存档信息</h2>
      <div class="archive-info" v-if="archiveList && archiveList.length > 0">
        <p>今日存档文件：</p>
        <ul class="archive-list">
          <li v-for="archive in todayArchives" :key="archive.filename">
            <span class="archive-type">{{ getTypeLabel(archive.season_type) }}</span>
            <span class="archive-size">{{ formatFileSize(archive.size) }}</span>
          </li>
        </ul>
      </div>
      <div class="archive-info" v-else-if="archiveList">
        <p>今日暂无存档</p>
      </div>
      <p v-else>加载中...</p>
    </div>

    <!-- 消息提示 -->
    <div class="message" v-if="message" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { refreshCache as refreshCacheApi, getAllCacheInfo, clearCache as clearCacheApi, getArchiveList } from '../api/stats'

const seasonTypes = ['all', 'league', 'cup']
const allCacheInfo = ref(null)
const archiveList = ref(null)
const loading = ref(false)
const message = ref('')
const messageType = ref('success')

const getTypeLabel = (type) => {
  const map = { all: '全部赛季', league: '联赛', cup: '杯赛' }
  return map[type] || type
}

const getCacheStatus = (type) => {
  if (!allCacheInfo.value || !allCacheInfo.value[type]) {
    return { valid: false, exists: false }
  }
  return {
    valid: allCacheInfo.value[type].is_valid,
    exists: allCacheInfo.value[type].exists
  }
}

const todayArchives = computed(() => {
  if (!archiveList.value) return []
  const today = new Date().toISOString().split('T')[0]
  return archiveList.value.filter(a => a.date === today)
})

const loadAllCacheInfo = async () => {
  try {
    const res = await getAllCacheInfo()
    allCacheInfo.value = res.data.data
  } catch (error) {
    console.error('获取缓存信息失败', error)
    message.value = '获取缓存信息失败：' + error.message
    messageType.value = 'error'
  }
}

const loadArchiveList = async () => {
  try {
    const res = await getArchiveList()
    archiveList.value = res.data.data.archives
  } catch (error) {
    console.error('获取存档列表失败', error)
  }
}

const refreshAll = async () => {
  loading.value = true
  message.value = ''
  try {
    for (const type of seasonTypes) {
      await refreshCacheApi(type, true)
    }
    message.value = '全部缓存刷新成功'
    messageType.value = 'success'
    await loadAllCacheInfo()
  } catch (error) {
    console.error('刷新缓存失败', error)
    message.value = '刷新缓存失败：' + error.message
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const refreshCache = async (type) => {
  loading.value = true
  message.value = ''
  try {
    const res = await refreshCacheApi(type, true)
    message.value = `${getTypeLabel(type)}缓存刷新成功`
    messageType.value = 'success'
    await loadAllCacheInfo()
  } catch (error) {
    console.error('刷新缓存失败', error)
    message.value = '刷新缓存失败：' + error.message
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const clearAll = async () => {
  if (!confirm('确定要清除所有缓存吗？')) return
  
  loading.value = true
  message.value = ''
  try {
    await clearCacheApi('all')
    message.value = '所有缓存已清除'
    messageType.value = 'success'
    await loadAllCacheInfo()
  } catch (error) {
    console.error('清除缓存失败', error)
    message.value = '清除缓存失败：' + error.message
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const clearCache = async (type) => {
  if (!confirm(`确定要清除${getTypeLabel(type)}的缓存吗？`)) return
  
  loading.value = true
  message.value = ''
  try {
    await clearCacheApi(type)
    message.value = `${getTypeLabel(type)}缓存已清除`
    messageType.value = 'success'
    await loadAllCacheInfo()
  } catch (error) {
    console.error('清除缓存失败', error)
    message.value = '清除缓存失败：' + error.message
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const formatTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  loadAllCacheInfo()
  loadArchiveList()
})
</script>

<style scoped>
.cache-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
}

.cache-status-item {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-lg);
}

.cache-status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--gray-200);
}

.cache-type-label {
  font-weight: var(--font-weight-bold);
  color: var(--gray-700);
  font-size: var(--font-size-lg);
}

.cache-status-details p {
  margin: var(--spacing-xs) 0;
  font-size: var(--font-size-sm);
  color: var(--gray-600);
}

.cache-status-details .label {
  font-weight: var(--font-weight-medium);
}

.cache-status-empty {
  text-align: center;
  color: var(--gray-500);
  padding: var(--spacing-lg) 0;
}

.single-cache-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.single-cache-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--gray-50);
  border-radius: var(--border-radius-md);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-sm);
}

.archive-list {
  list-style: none;
  padding: 0;
  margin: var(--spacing-md) 0 0 0;
}

.archive-list li {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--gray-100);
  font-size: var(--font-size-sm);
}

.archive-type {
  font-weight: var(--font-weight-medium);
  color: var(--primary-medium);
}

.archive-size {
  color: var(--gray-600);
}

@media (max-width: 768px) {
  .cache-overview {
    grid-template-columns: 1fr;
  }

  .single-cache-action {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }

  .single-cache-action .action-buttons {
    width: 100%;
    display: flex;
    gap: var(--spacing-sm);
  }

  .single-cache-action .btn {
    flex: 1;
  }
}
</style>
