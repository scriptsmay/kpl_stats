<template>
  <div class="match-records-page">
    <div class="page-header">
      <h1 class="page-title">🎬 比赛高光记录</h1>
      <p class="page-subtitle">无言职业生涯精彩瞬间</p>
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
    <div class="records-container" v-else-if="records.length > 0">
      <div class="record-card" v-for="record in records" :key="record.id">
        <!-- 视频封面 -->
        <div class="record-cover" @click="playVideo(record)">
          <img :src="record.cover" :alt="record.title" @error="handleCoverError" />
          <div class="play-icon">▶</div>
          <div class="record-duration" v-if="record.duration">{{ record.duration }}</div>
        </div>

        <!-- 记录信息 -->
        <div class="record-info">
          <h3 class="record-title">{{ record.title }}</h3>
          <p class="record-date">{{ record.date }}</p>
          <p class="record-description">{{ record.description }}</p>

          <!-- 标签 -->
          <div class="record-tags" v-if="record.tags">
            <span class="tag" v-for="tag in record.tags" :key="tag">{{ tag }}</span>
          </div>

          <!-- 操作按钮 -->
          <div class="record-actions">
            <button class="btn btn-secondary" @click="playVideo(record)">
              ▶ 播放视频
            </button>
            <a :href="record.videoUrl" target="_blank" class="btn btn-outline" v-if="record.videoUrl">
              🔗 外链观看
            </a>
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

    <!-- 视频播放弹窗 -->
    <div class="video-modal" v-if="currentVideo" @click="closeVideo">
      <div class="video-content" @click.stop>
        <button class="close-btn" @click="closeVideo">×</button>
        <video ref="videoPlayer" controls autoplay :poster="currentVideo.cover">
          <source :src="currentVideo.videoUrl" type="video/mp4" />
          您的浏览器不支持视频播放
        </video>
        <h2 class="video-title">{{ currentVideo.title }}</h2>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getMatchRecords } from '../api/stats';

const loading = ref(false);
const error = ref(null);
const records = ref([]);
const currentVideo = ref(null);
const videoPlayer = ref(null);

// 加载高光记录
const loadRecords = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getMatchRecords();
    // 后端返回的数据格式：{ code: 200, data: [{ date, game_number, team1, team2, tournament, content, active, record_id }] }
    const apiRecords = res.data.data || [];
    // 转换为前端需要的格式
    records.value = apiRecords.map((item, index) => ({
      id: item.record_id || index,
      title: `${item.team1} vs ${item.team2}`,
      date: item.date,
      description: formatContent(item.content),
      cover: extractImageFromContent(item.content),
      videoUrl: '', // 第三方 API 未提供视频 URL，后续可扩展
      duration: '',
      tags: [item.tournament, `第${item.game_number}局`],
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

// 从 content 中提取文字描述（去除图片链接和多余空格）
const formatContent = (content) => {
  if (!content) return '';
  // 移除图片链接
  const withoutImages = content.replace(/https?:\/\/\S+\.(jpg|jpeg|png|gif|webp)\S*/gi, '');
  // 移除 [星星] 等特殊符号
  const withoutSymbols = withoutImages.replace(/\[.*?\]/g, '');
  // 压缩多余空格和换行
  return withoutSymbols.replace(/\s+/g, ' ').trim().slice(0, 200);
};

// 从 content 中提取图片 URL 作为封面
const extractImageFromContent = (content) => {
  if (!content) return '';
  // 匹配图片 URL
  const imageMatch = content.match(/https?:\/\/\S+\.(jpg|jpeg|png|gif|webp)\S*/i);
  return imageMatch ? imageMatch[0] : '';
};

// 播放视频
const playVideo = (record) => {
  if (record.videoUrl) {
    currentVideo.value = record;
  } else {
    alert('该视频暂不支持在线播放');
  }
};

// 关闭视频
const closeVideo = () => {
  currentVideo.value = null;
};

// 封面图加载失败处理
const handleCoverError = (e) => {
  e.target.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
};

onMounted(() => {
  loadRecords();
});
</script>

<style scoped>
.match-records-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

/* 页面头部 */
.page-header {
  text-align: center;
  margin-bottom: var(--spacing-xxl);
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.page-subtitle {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
}

/* 记录列表 */
.records-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-xl);
}

.record-card {
  background: var(--white);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}

.record-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

/* 视频封面 */
.record-cover {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 比例 */
  background: var(--gray-100);
  cursor: pointer;
  overflow: hidden;
}

.record-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--transition-base);
}

.record-cover:hover img {
  transform: scale(1.05);
}

.play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: rgba(30, 58, 138, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--white);
  font-size: 24px;
  opacity: 0;
  transition: opacity var(--transition-base);
}

.record-cover:hover .play-icon {
  opacity: 1;
}

.record-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: var(--white);
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
}

/* 记录信息 */
.record-info {
  padding: var(--spacing-lg);
}

.record-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.record-date {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-md);
}

.record-description {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: var(--spacing-md);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 标签 */
.record-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.tag {
  background: var(--primary-light);
  color: var(--primary-medium);
  padding: 4px 12px;
  border-radius: var(--border-radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

/* 操作按钮 */
.record-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

/* 视频弹窗 */
.video-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-xl);
}

.video-content {
  position: relative;
  max-width: 900px;
  width: 100%;
  background: var(--gray-900);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  border-radius: 50%;
  color: var(--white);
  font-size: 24px;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--transition-base);
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.9);
}

.video-content video {
  width: 100%;
  height: auto;
  display: block;
}

.video-title {
  padding: var(--spacing-lg);
  color: var(--white);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: var(--spacing-xxl);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-lg);
}

.empty-text {
  font-size: var(--font-size-xl);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.empty-hint {
  font-size: var(--font-size-base);
  color: var(--text-tertiary);
}
</style>
