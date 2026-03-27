<template>
  <div class="match-records-page">
    <div class="match-records-header">
      <h1 class="match-records-title">🎬 比赛高光记录</h1>
      <p class="match-records-subtitle">无言职业生涯精彩瞬间</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载高光记录...</div>
    </div>

    <!-- 错误状态 -->
    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadRecords">重试</button>
    </div>

    <!-- 数据列表 -->
    <div class="match-records-list" v-else-if="records.length > 0">
      <div class="match-record-card" v-for="record in records" :key="record.id">
        <!-- 左侧封面图 -->
        <div class="match-record-cover">
          <img v-if="record.cover" :src="record.cover" :alt="record.title" @error="handleCoverError" />
          <div class="placeholder" v-else>📷</div>
        </div>

        <!-- 右侧内容 -->
        <div class="match-record-content">
          <h3 class="match-record-title">{{ record.title }}</h3>
          
          <div class="match-record-meta">
            <span class="match-record-date">📅 {{ record.date }}</span>
            <span class="match-record-tournament">{{ record.tournament }}</span>
          </div>

          <p class="match-record-description">{{ record.description }}</p>

          <div class="match-record-tags">
            <span class="match-record-tag">第{{ record.gameNumber }}局</span>
            <span class="match-record-tag" :class="{ 'tag-active': record.active }">
              {{ record.active ? '高光' : '记录' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <div class="empty-icon">🎬</div>
      <p class="empty-text">暂无高光记录</p>
      <p class="empty-hint">精彩瞬间正在收集中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getMatchRecords } from '../api/stats';

const loading = ref(false);
const error = ref(null);
const records = ref([]);

// 加载高光记录
const loadRecords = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getMatchRecords();
    const apiRecords = res.data.data || [];
    
    // 转换为前端需要的格式
    records.value = apiRecords.map((item, index) => ({
      id: item.record_id || index,
      title: `${item.team1} vs ${item.team2}`,
      date: item.date,
      tournament: item.tournament,
      gameNumber: item.game_number,
      active: item.active,
      description: formatContent(item.content),
      cover: extractImageFromContent(item.content),
      rawContent: item.content
    }));
    
    console.log('高光记录加载成功', records.value);
  } catch (err) {
    console.error('加载失败', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
  }
};

// 从 content 中提取文字描述（保留换行，去除图片链接）
const formatContent = (content) => {
  if (!content) return '';
  // 移除图片链接
  const withoutImages = content.replace(/https?:\/\/\S+\.(jpg|jpeg|png|gif|webp)\S*/gi, '');
  // 移除 [星星] 等特殊符号
  const withoutSymbols = withoutImages.replace(/\[.*?\]/g, '');
  // 保留换行，压缩多余空格
  return withoutSymbols.replace(/[ \t]+/g, ' ').trim();
};

// 从 content 中提取图片 URL 作为封面
const extractImageFromContent = (content) => {
  if (!content) return '';
  const imageMatch = content.match(/https?:\/\/\S+\.(jpg|jpeg|png|gif|webp)\S*/i);
  return imageMatch ? imageMatch[0] : '';
};

// 封面图加载失败处理
const handleCoverError = (e) => {
  e.target.style.display = 'none';
  e.target.nextElementSibling?.classList.remove('hidden');
};

onMounted(() => {
  loadRecords();
});
</script>
