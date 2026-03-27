<template>
  <div class="result-section match-records-page">
    <div class="result-header match-records-header">
      <h1 class="result-title">📷 比赛高光记录</h1>
      <p class="result-subtitle">无言职业生涯精彩瞬间</p>
    </div>

    <!-- 赛季筛选 -->
    <div class="season-filter-container" v-if="seasons.length > 0">
      <button class="season-filter-btn" :class="{ active: selectedSeason === 'all' }" @click="filterSeason('all')">
        📊 全部赛季
      </button>
      <button
        v-for="season in seasons"
        :key="season.season_id"
        class="season-filter-btn"
        :class="{ active: selectedSeason === season.season_id }"
        @click="filterSeason(season.season_id)"
      >
        {{ season.season_name }}
      </button>
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
      <div
        class="match-record-card"
        :class="{ 'is-highlight': record.isHighlight }"
        v-for="record in records"
        :key="record.id"
      >
        <!-- 左侧封面图 -->
        <div class="match-record-cover">
          <img v-if="record.cover" :src="record.cover" :alt="record.title" @error="handleCoverError" />
          <div class="placeholder" v-else>📷</div>
        </div>

        <!-- 右侧内容 -->
        <div class="match-record-content">
          <div class="match-record-header">
            <h3 class="match-record-title">{{ record.title }}</h3>
            <div class="match-record-tags">
              <span class="match-record-tag">第{{ record.gameNumber }}局</span>
              <span class="match-record-tag" :class="{ 'tag-active': record.isHighlight }">
                {{ record.isHighlight ? '⭐ MVP' : '📝 记录' }}
              </span>
            </div>
          </div>

          <div class="match-record-meta">
            <span class="match-record-date">📅 {{ record.date }}</span>
            <span class="match-record-tournament">{{ record.tournament }}</span>
          </div>

          <p class="match-record-description">{{ record.description }}</p>
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
import { getMatchRecords, getPlayerSeasons } from '../api/stats';

const loading = ref(false);
const error = ref(null);
const records = ref([]);
const seasons = ref([]);
const selectedSeason = ref('all');

// 加载选手参赛赛季列表
const loadSeasons = async () => {
  try {
    const res = await getPlayerSeasons();
    seasons.value = res.data.data || [];
    console.log('赛季列表加载成功', seasons.value);
  } catch (err) {
    console.error('加载赛季列表失败', err);
    // 使用默认赛季
    seasons.value = [
      { season_id: 'KPL2026S1', season_name: '2026 年春季赛' },
      { season_id: 'KCC2025', season_name: '2025 挑战者杯' },
    ];
  }
};

// 加载高光记录
const loadRecords = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getMatchRecords(selectedSeason.value);
    const apiRecords = res.data.data || [];

    // 转换为前端需要的格式
    records.value = apiRecords.map((item, index) => ({
      id: item.record_id || index,
      title: `${item.team1} vs ${item.team2}`,
      date: item.date,
      tournament: item.tournament,
      gameNumber: item.game_number,
      isHighlight: isHighlightRecord(item.content),
      description: formatContent(item.content),
      cover: extractImageFromContent(item.content),
      rawContent: item.content,
    }));

    console.log('高光记录加载成功', records.value);
  } catch (err) {
    console.error('加载失败', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
  }
};

// 筛选赛季
const filterSeason = async (seasonId) => {
  if (seasonId === selectedSeason.value) return;
  selectedSeason.value = seasonId;
  await loadRecords();
};

// 从 content 中提取文字描述（保留换行和星星符号，去除图片链接）
const formatContent = (content) => {
  if (!content) return '';
  // 移除图片链接
  const withoutImages = content.replace(/https?:\/\/\S+\.(jpg|jpeg|png|gif|webp)\S*/gi, '');
  // 将 [星星] 替换为 ⭐ + 空格
  const withStars = withoutImages.replace(/\[星星\]/g, '⭐ ');
  // 压缩多余空格（保留换行）
  return withStars.replace(/[ \t]+/g, ' ').trim();
};

// 判断是否为高光记录（content 中含有 "MVP 为 xxx 无言" 或 "MVP 为@无言" 等）
const isHighlightRecord = (content) => {
  if (!content) return false;
  // 匹配 MVP 为 xxx 无言 的格式，如 "MVP 为@KSG 无言_ (赵昊宇) 关羽"
  // 使用 .*? 非贪婪匹配任意字符（包括 @、_、括号等）
  return /MVP为.*?无言/i.test(content);
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
  loadSeasons();
  loadRecords();
});
</script>
