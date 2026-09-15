<template>
  <div class="admin-panel">
    <h1>前端缓存管理</h1>

    <div class="admin-card">
      <h2>本地缓存</h2>
      <p>所有数据由静态文件托管，前端会进行本地缓存加速访问。</p>
      <div class="action-buttons">
        <button @click="clearFrontendCache" class="btn btn-danger">
          清除本地缓存
        </button>
      </div>
    </div>

    <!-- 消息提示 -->
    <div class="message" v-if="message" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { clearDataCache } from '../api/github-data'

const message = ref('')
const messageType = ref('success')

const clearFrontendCache = () => {
  if (!confirm('确定要清除前端本地缓存吗？这会导致下次访问重新拉取数据。')) return
  
  clearDataCache()
  message.value = '本地缓存已清除'
  messageType.value = 'success'
}
</script>

<style scoped>
.admin-panel {
  max-width: 800px;
  margin: 0 auto;
}

.admin-card {
  background: white;
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.action-buttons {
  margin-top: var(--spacing-md);
  display: flex;
  gap: var(--spacing-md);
}

.message {
  padding: var(--spacing-md);
  border-radius: var(--border-radius-md);
  margin-top: var(--spacing-lg);
  text-align: center;
}

.success {
  background-color: #d4edda;
  color: #155724;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
}
</style>
