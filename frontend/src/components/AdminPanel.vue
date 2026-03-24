<template>
  <div class="admin-panel">
    <h3>数据管理</h3>
    <div class="button-group">
      <button @click="refreshData" :disabled="loading">
        {{ loading ? '刷新中...' : '手动刷新数据' }}
      </button>
      <button @click="clearCacheData" :disabled="loading">清除缓存</button>
      <button @click="showCacheInfo">查看缓存信息</button>
    </div>

    <div v-if="cacheInfo" class="cache-info">
      <h4>缓存信息</h4>
      <pre>{{ JSON.stringify(cacheInfo, null, 2) }}</pre>
    </div>

    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { refreshCache, clearCache, getCacheInfo, getCareerData } from '../api/stats';

const loading = ref(false);
const message = ref('');
const messageType = ref('');
const cacheInfo = ref(null);

const showMessage = (text, type = 'success') => {
  message.value = text;
  messageType.value = type;
  setTimeout(() => {
    message.value = '';
  }, 3000);
};

const refreshData = async () => {
  loading.value = true;
  try {
    const res = await refreshCache(true);
    showMessage(`刷新成功！更新时间：${res.data.data.refresh_time}`);
    // 刷新后重新加载页面数据
    window.location.reload();
  } catch (error) {
    showMessage(`刷新失败：${error.message}`, 'error');
  } finally {
    loading.value = false;
  }
};

const clearCacheData = async () => {
  loading.value = true;
  try {
    const res = await clearCache();
    showMessage(res.data.message);
  } catch (error) {
    showMessage(`清除失败：${error.message}`, 'error');
  } finally {
    loading.value = false;
  }
};

const showCacheInfo = async () => {
  try {
    const res = await getCacheInfo();
    cacheInfo.value = res.data.data;
  } catch (error) {
    showMessage(`获取失败：${error.message}`, 'error');
  }
};
</script>

<style scoped>
.admin-panel {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.cache-info {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
}

.cache-info pre {
  margin: 0;
  font-size: 12px;
  overflow-x: auto;
}

.message {
  margin-top: 10px;
  padding: 10px;
  border-radius: 4px;
}

.message.success {
  background: #d4edda;
  color: #155724;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
}
</style>
