<template>
  <div class="result-section" style="display: block" v-if="careerData">
    <div class="result-header">
      <div class="result-title">选手生涯数据</div>
    </div>

    <!-- 赛季筛选 -->
    <div class="season-filter-container">
      <button
        class="season-filter-btn active"
        @click="filterSeasonType('all')"
        :class="{ active: seasonFilter === 'all' }"
      >
        📊 全部赛季
      </button>
      <button
        class="season-filter-btn"
        @click="filterSeasonType('league')"
        :class="{ active: seasonFilter === 'league' }"
      >
        🏆 联赛
      </button>
      <button class="season-filter-btn" @click="filterSeasonType('cup')" :class="{ active: seasonFilter === 'cup' }">
        🏅 杯赛
      </button>
    </div>

    <!-- 选手卡片 -->
    <div class="player-card-container single">
      <div class="player-card">
        <img :src="playerAvatar" :alt="careerData.player_info.latest_nickname" @error="handleAvatarError" />
        <div class="player-card-name">{{ careerData.player_info.latest_nickname }}</div>
        <div class="player-card-info">{{ careerData.player_info.latest_team }}</div>
        <div class="player-card-info">{{ careerData.player_info.position || '位置未知' }}</div>
        <div class="player-card-info">筛选：{{ seasonFilterText }}</div>
      </div>
    </div>

    <!-- 职业生涯信息卡 -->
    <div class="career-info-card">
      <div class="career-info-item">
        <span class="career-info-label">职业生涯时间</span>
        <span class="career-info-value">{{ careerData.career_summary.date_range }}</span>
      </div>
      <div class="career-info-item">
        <span class="career-info-label">参与赛季总数</span>
        <span class="career-info-value">{{ getSeasonSummary() }}</span>
      </div>
    </div>

    <!-- 总数据概览 -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.total_matches }}</div>
        <div class="summary-card-label">生涯总对局</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value win">{{ careerData.career_summary.win_battles }}</div>
        <div class="summary-card-label">获胜对局</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value lose">{{ careerData.career_summary.lose_battles }}</div>
        <div class="summary-card-label">失败对局</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.match_win_rate }}</div>
        <div class="summary-card-label">对局胜率</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.total_kills }}</div>
        <div class="summary-card-label">生涯总击杀</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.total_deaths }}</div>
        <div class="summary-card-label">生涯总死亡</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.total_assists }}</div>
        <div class="summary-card-label">生涯总助攻</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.kda_ratio }}</div>
        <div class="summary-card-label">生涯 KDA 比</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.avg_kills }}</div>
        <div class="summary-card-label">场均击杀</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.avg_deaths }}</div>
        <div class="summary-card-label">场均死亡</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.avg_assists }}</div>
        <div class="summary-card-label">场均助攻</div>
      </div>
    </div>

    <!-- 大场数据 -->
    <div class="data-category-tabs">
      <div class="category-tab active">大场数据</div>
    </div>

    <div class="summary-cards">
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.total_series || 0 }}</div>
        <div class="summary-card-label">总大场数</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value win">{{ careerData.career_summary.series_wins || 0 }}</div>
        <div class="summary-card-label">大场获胜</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value lose">{{ careerData.career_summary.series_losses || 0 }}</div>
        <div class="summary-card-label">大场失败</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary.series_win_rate || '0%' }}</div>
        <div class="summary-card-label">大场胜率</div>
      </div>
    </div>

    <!-- 大场记录 -->
    <div id="cooperation-match-container">
      <div id="cooperation-match-anchor" class="scroll-anchor"></div>
      <div class="section-title">大场记录 (共{{ filteredMatchDetails.length }}场)</div>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>比赛日期</th>
              <th>赛季</th>
              <th>我方战队</th>
              <th>对手战队</th>
              <th class="center">小局数</th>
              <th class="center">获胜小局</th>
              <th class="center">失败小局</th>
              <th class="center">大场结果</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="match in paginatedMatches" :key="match.match_id">
              <td>{{ match.match_date }}</td>
              <td>{{ match.season_name || match.season_id }}</td>
              <td>{{ match.team_name }}</td>
              <td>{{ match.opponent_team_name }}</td>
              <td class="center">
                <strong>{{ match.total_games }}</strong>
              </td>
              <td class="center">
                <span class="win-number">{{ match.wins }}</span>
              </td>
              <td class="center">
                <span class="lose-number">{{ match.losses }}</span>
              </td>
              <td class="center">
                <span :class="['win-badge', match.match_is_win ? 'win' : 'lose']">
                  {{ match.match_is_win ? '胜利' : '失败' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 分页 -->
      <div class="pagination-container" v-if="totalPages > 1">
        <button class="pagination-btn" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
          上一页
        </button>
        <button
          v-for="page in displayPages"
          :key="page"
          :class="['pagination-btn', { active: currentPage === page }]"
          @click="changePage(page)"
        >
          {{ page }}
        </button>
        <button class="pagination-btn" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
          下一页
        </button>
        <span class="pagination-info">共 {{ totalPages }} 页</span>
      </div>
    </div>

    <!-- 效力战队统计 -->
    <div class="section-title">效力战队统计</div>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>战队名称</th>
            <th class="center">对局数</th>
            <th class="center">胜局</th>
            <th class="center">败局</th>
            <th class="center">胜率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in careerData.team_stats" :key="team.team_name">
            <td>
              <strong>{{ team.team_name }}</strong>
            </td>
            <td class="center">{{ team.battles }}</td>
            <td class="center">
              <span class="win-number">{{ team.wins }}</span>
            </td>
            <td class="center">
              <span class="lose-number">{{ team.loses }}</span>
            </td>
            <td class="center">
              <strong>{{ team.win_rate }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 赛季数据统计 -->
    <div class="section-title">赛季数据统计</div>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>赛季</th>
            <th class="center">对局数</th>
            <th class="center">胜局</th>
            <th class="center">败局</th>
            <th class="center">胜率</th>
            <th class="center">击杀/死亡/助攻</th>
            <th class="center">KDA 比</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="season in filteredSeasonStats" :key="season.season_id">
            <td>{{ season.season_name || season.season_id }}</td>
            <td class="center">
              <strong>{{ season.battles }}</strong>
            </td>
            <td class="center">
              <span class="win-number">{{ season.wins }}</span>
            </td>
            <td class="center">
              <span class="lose-number">{{ season.loses }}</span>
            </td>
            <td class="center">{{ season.win_rate }}</td>
            <td class="center">{{ season.kills }}/{{ season.deaths }}/{{ season.assists }}</td>
            <td class="center">
              <strong>{{ season.kda_ratio }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 英雄使用统计 -->
    <div class="section-title">英雄使用统计 (共{{ careerData.hero_stats.length }}个英雄)</div>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>英雄</th>
            <th class="center">使用次数</th>
            <th class="center">胜局</th>
            <th class="center">败局</th>
            <th class="center">胜率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="hero in careerData.hero_stats" :key="hero.hero_id">
            <td>
              <div class="hero-info">
                <img
                  :src="getHeroAvatar(hero.hero_name)"
                  :alt="hero.hero_name"
                  class="hero-icon"
                  @error="handleHeroAvatarError($event)"
                />
                <strong>{{ hero.hero_name }}</strong>
              </div>
            </td>
            <td class="center">
              <strong>{{ hero.battles }}</strong>
            </td>
            <td class="center">
              <span class="win-number">{{ hero.wins }}</span>
            </td>
            <td class="center">
              <span class="lose-number">{{ hero.loses }}</span>
            </td>
            <td class="center">
              <strong>{{ hero.win_rate }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- 加载状态 -->
  <div class="loading" v-else>
    <div class="loading-spinner"></div>
    <div class="loading-text">正在加载数据...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const careerData = ref(null);
const seasonFilter = ref('all');
const currentPage = ref(1);
const pageSize = 10;

const playerAvatar = ref('https://hero-wind.oss-cn-shanghai.aliyuncs.com/KPL/KPL_Play_images/KPL2026S1/KSG.无言.png');

const seasonFilterText = computed(() => {
  const map = { all: '全部赛季', league: '联赛', cup: '杯赛' };
  return map[seasonFilter.value];
});

// 筛选后的比赛详情
const filteredMatchDetails = computed(() => {
  if (!careerData.value) return [];
  const matches = careerData.value.match_details || [];
  if (seasonFilter.value === 'all') return matches;

  return matches.filter((match) => {
    const seasonName = match.season_name || match.season_id || '';
    if (seasonFilter.value === 'league') {
      return seasonName.includes('KPL') || seasonName.includes('联赛');
    } else if (seasonFilter.value === 'cup') {
      return seasonName.includes('杯') || seasonName.includes('挑战者杯');
    }
    return true;
  });
});

// 分页后的比赛
const paginatedMatches = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredMatchDetails.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredMatchDetails.value.length / pageSize);
});

// 显示的页码
const displayPages = computed(() => {
  const pages = [];
  const total = totalPages.value;
  const current = currentPage.value;

  for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
    pages.push(i);
  }
  return pages;
});

// 筛选后的赛季数据
const filteredSeasonStats = computed(() => {
  if (!careerData.value) return [];
  const stats = careerData.value.season_stats || [];
  if (seasonFilter.value === 'all') return stats;

  return stats.filter((season) => {
    const seasonName = season.season_name || season.season_id || '';
    if (seasonFilter.value === 'league') {
      return seasonName.includes('KPL') || seasonName.includes('联赛');
    } else if (seasonFilter.value === 'cup') {
      return seasonName.includes('杯') || seasonName.includes('挑战者杯');
    }
    return true;
  });
});

const filterSeasonType = (type) => {
  seasonFilter.value = type;
  currentPage.value = 1;
};

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
};

const handleAvatarError = (e) => {
  e.target.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
};

const handleHeroAvatarError = (e) => {
  e.target.style.display = 'none';
};

const getHeroAvatar = (heroName) => {
  // 这里可以根据英雄名字映射到具体的头像 URL
  // 暂时返回一个默认占位图
  return '';
};

const getSeasonSummary = () => {
  if (!careerData.value) return '';
  const total = careerData.value.season_stats?.length || 0;
  const leagueCount = filteredSeasonStats.value.filter((s) => {
    const name = s.season_name || s.season_id || '';
    return name.includes('KPL') || name.includes('联赛');
  }).length;
  const cupCount = total - leagueCount;
  return `${total} 个赛季（联赛：${leagueCount}，杯赛：${cupCount}）`;
};

onMounted(async () => {
  try {
    const res = await axios.get('/api/player/career');
    careerData.value = res.data.data;
    console.log('数据加载成功', careerData.value);
  } catch (error) {
    console.error('加载失败', error);
  }
});
</script>

<style scoped>
.result-section {
  padding: 40px;
}

.result-header {
  border-bottom: 3px solid #2a5298;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  display: flex;
}

.result-title {
  color: #333;
  font-size: 24px;
  font-weight: 700;
}

/* 赛季筛选 */
.season-filter-container {
  z-index: 100;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 2px solid #dee2e6;
  border-radius: 10px;
  justify-content: center;
  gap: 15px;
  margin-bottom: 25px;
  padding: 15px 20px;
  display: flex;
}

.season-filter-btn {
  color: #2a5298;
  cursor: pointer;
  background: #fff;
  border: 2px solid #2a5298;
  border-radius: 8px;
  min-width: 110px;
  padding: 10px 25px;
  font-size: 15px;
  font-weight: 700;
  transition: all 0.3s;
}

.season-filter-btn:hover {
  background: #f0f4f8;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px #2a529833;
}

.season-filter-btn.active {
  color: #fff;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}

/* 选手卡片 */
.player-card-container {
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 30px;
  margin-bottom: 40px;
  display: grid;
}

.player-card-container.single {
  grid-template-columns: 1fr;
}

.player-card {
  color: #fff;
  text-align: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 15px;
  padding: 25px;
  max-width: 400px;
  margin: 0 auto;
}

.player-card img {
  object-fit: cover;
  border: 4px solid #fff;
  border-radius: 50%;
  width: 100px;
  height: 100px;
  margin-bottom: 15px;
}

.player-card-name {
  margin-bottom: 8px;
  font-size: 20px;
  font-weight: 700;
}

.player-card-info {
  opacity: 0.9;
  font-size: 14px;
  margin: 4px 0;
}

/* 职业生涯信息卡 */
.career-info-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 2px solid #dee2e6;
  border-radius: 12px;
  margin-bottom: 30px;
  padding: 20px;
}

.career-info-item {
  border-bottom: 1px solid #dee2e6;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  display: flex;
}

.career-info-item:last-child {
  border-bottom: none;
}

.career-info-label {
  color: #666;
  flex-shrink: 0;
  min-width: 100px;
  padding-right: 20px;
  font-size: 14px;
}

.career-info-value {
  color: #333;
  text-align: right;
  flex: 1;
  font-size: 14px;
  font-weight: 700;
}

/* 数据概览卡片 */
.summary-cards {
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
  display: grid;
}

.summary-card {
  text-align: center;
  background: #1e3c720d;
  border: 2px solid #1e3c721a;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s;
}

.summary-card:hover {
  border-color: #1e3c724d;
  box-shadow: 0 4px 12px #1e3c721a;
}

.summary-card-value {
  color: #2a5298;
  margin-bottom: 8px;
  font-size: 32px;
  font-weight: 700;
}

.summary-card-value.win {
  color: #28a745;
}

.summary-card-value.lose {
  color: #dc3545;
}

.summary-card-label {
  color: #666;
  font-size: 14px;
}

/* 分类标签 */
.data-category-tabs {
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
  display: flex;
}

.category-tab {
  color: #2a5298;
  background: #fff;
  border: 2px solid #2a5298;
  border-radius: 8px;
  padding: 10px 25px;
  font-size: 14px;
  font-weight: 700;
}

.category-tab.active {
  color: #fff;
  background: #2a5298;
}

/* 章节标题 */
.section-title {
  color: #333;
  border-bottom: 2px solid #2a5298;
  margin: 30px 0 20px;
  padding-bottom: 10px;
  font-size: 20px;
  font-weight: 700;
}

/* 表格 */
.table-container {
  margin-bottom: 30px;
  overflow-x: auto;
}

.data-table {
  border-collapse: collapse;
  background: #fff;
  border-radius: 12px;
  width: 100%;
  overflow: hidden;
}

.data-table thead {
  color: #fff;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}

.data-table th {
  text-align: left;
  padding: 15px;
  font-weight: 700;
}

.data-table th.center,
.data-table td.center {
  text-align: center;
}

.data-table td {
  border-bottom: 1px solid #f0f0f0;
  padding: 12px 15px;
}

.data-table tbody tr:hover {
  background: #f8f9fa;
}

/* 英雄信息 */
.hero-info {
  align-items: center;
  gap: 8px;
  display: flex;
}

.hero-icon {
  object-fit: cover;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 32px;
  height: 32px;
}

/* 胜负徽章 */
.win-badge {
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 700;
  display: inline-block;
}

.win-badge.win {
  color: #155724;
  background: #d4edda;
}

.win-badge.lose {
  color: #721c24;
  background: #f8d7da;
}

/* 数字样式 */
.win-number {
  color: #28a745;
  font-weight: 700;
}

.lose-number {
  color: #dc3545;
  font-weight: 700;
}

/* 分页 */
.pagination-container {
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 20px 0;
  display: flex;
}

.pagination-btn {
  color: #2a5298;
  cursor: pointer;
  background: #fff;
  border: 2px solid #2a5298;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.3s;
}

.pagination-btn:hover:not(:disabled) {
  color: #fff;
  background: #2a5298;
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination-btn.active {
  color: #fff;
  background: #2a5298;
}

.pagination-info {
  color: #666;
  margin: 0 10px;
  font-size: 14px;
}

/* 加载状态 */
.loading {
  text-align: center;
  color: #2a5298;
  padding: 60px 40px;
}

.loading-spinner {
  border: 6px solid #f3f3f3;
  border-top-color: #2a5298;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
  animation: 1s linear infinite spin;
  display: inline-block;
}

@keyframes spin {
  0% {
    transform: rotate(0);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: 700;
}

/* 滚动锚点 */
.scroll-anchor {
  scroll-margin-top: 20px;
}

/* 响应式 */
@media (max-width: 768px) {
  .result-section {
    padding: 20px 15px;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .result-title {
    font-size: 20px;
  }

  .season-filter-container {
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 10px;
  }

  .season-filter-btn {
    flex: 1;
    min-width: calc(33.333% - 6px);
    padding: 8px 12px;
    font-size: 13px;
  }

  .player-card {
    padding: 20px;
  }

  .player-card img {
    width: 80px;
    height: 80px;
  }

  .player-card-name {
    font-size: 18px;
  }

  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 25px;
  }

  .summary-card {
    padding: 15px 12px;
  }

  .summary-card-value {
    font-size: 24px;
  }

  .summary-card-label {
    font-size: 12px;
  }

  .data-table {
    min-width: 600px;
    font-size: 13px;
  }

  .data-table th,
  .data-table td {
    padding: 10px 8px;
  }

  .hero-icon {
    width: 28px;
    height: 28px;
  }

  .career-info-card {
    margin-bottom: 20px;
    padding: 15px;
  }

  .career-info-item {
    flex-direction: column;
    align-items: flex-start;
    padding: 6px 0;
  }

  .career-info-label {
    min-width: auto;
    margin-bottom: 5px;
    padding-right: 0;
    font-size: 13px;
  }

  .career-info-value {
    text-align: left;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }

  .season-filter-btn {
    min-width: 100%;
    font-size: 14px;
  }

  .data-table {
    min-width: 500px;
    font-size: 12px;
  }
}
</style>
