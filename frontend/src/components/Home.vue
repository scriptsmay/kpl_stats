<template>
  <div class="result-section" v-if="careerData">
    <div class="result-header">
      <div class="result-title">选手生涯数据</div>
    </div>

    <!-- 赛季筛选 -->
    <div class="season-filter-container">
      <button class="season-filter-btn" :class="{ active: seasonFilter === 'all' }" @click="filterSeasonType('all')">
        📊 全部赛季
      </button>
      <button
        class="season-filter-btn"
        :class="{ active: seasonFilter === 'league' }"
        @click="filterSeasonType('league')"
      >
        🏆 联赛
      </button>
      <button class="season-filter-btn" :class="{ active: seasonFilter === 'cup' }" @click="filterSeasonType('cup')">
        🏅 杯赛
      </button>
    </div>

    <div class="flex flex-wrap">
      <!-- 选手卡片 -->
      <div class="player-card-container single">
        <div class="player-card">
          <img
            :src="playerAvatar"
            :alt="careerData.player_info?.latest_nickname || '选手'"
            @error="handleAvatarError"
          />
          <div class="player-card-name">{{ careerData.player_info?.latest_nickname || '未知' }}</div>
          <div class="player-card-info">{{ careerData.player_info?.latest_team || '未知战队' }}</div>
          <div class="player-card-info">{{ careerData.player_info?.position || '对抗路' }}</div>
          <div class="player-card-info">筛选：{{ seasonFilterText }}</div>
        </div>
      </div>

      <!-- 职业生涯信息卡 -->
      <div class="career-info-card flex-item">
        <div class="career-info-item">
          <span class="career-info-label">职业生涯时间</span>
          <span class="career-info-value">{{ careerData.career_summary?.date_range || '-' }}</span>
        </div>
        <div class="career-info-item">
          <span class="career-info-label">参与赛季总数</span>
          <span class="career-info-value">{{ getSeasonSummary() }}</span>
        </div>
      </div>
    </div>

    <!-- 总数据概览 -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.total_battles || 0 }}</div>
        <div class="summary-card-label">生涯总对局</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value win">{{ careerData.career_summary?.win_battles || 0 }}</div>
        <div class="summary-card-label">获胜对局</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value lose">{{ careerData.career_summary?.lose_battles || 0 }}</div>
        <div class="summary-card-label">失败对局</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.win_rate || '0%' }}</div>
        <div class="summary-card-label">对局胜率</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.total_kills || 0 }}</div>
        <div class="summary-card-label">生涯总击杀</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.total_deaths || 0 }}</div>
        <div class="summary-card-label">生涯总死亡</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.total_assists || 0 }}</div>
        <div class="summary-card-label">生涯总助攻</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.kda_ratio || '0' }}</div>
        <div class="summary-card-label">生涯 KDA 比</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.avg_kills || '0' }}</div>
        <div class="summary-card-label">场均击杀</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.avg_deaths || '0' }}</div>
        <div class="summary-card-label">场均死亡</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.avg_assists || '0' }}</div>
        <div class="summary-card-label">场均助攻</div>
      </div>
    </div>

    <!-- 大场数据 -->
    <div class="data-category-tabs">
      <div class="category-tab active">大场数据</div>
    </div>

    <div class="summary-cards">
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.total_matches || 0 }}</div>
        <div class="summary-card-label">总大场数</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value win">{{ careerData.career_summary?.match_wins || 0 }}</div>
        <div class="summary-card-label">大场获胜</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value lose">{{ careerData.career_summary?.match_loses || 0 }}</div>
        <div class="summary-card-label">大场失败</div>
      </div>
      <div class="summary-card">
        <div class="summary-card-value">{{ careerData.career_summary?.match_win_rate || '0%' }}</div>
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
              <td>{{ getSeasonName(match.season_id) }}</td>
              <td>{{ match.team_name }}</td>
              <td>{{ match.opponent_team_name }}</td>
              <td class="center">
                <strong>{{ match.total_battles }}</strong>
              </td>
              <td class="center">
                <span class="win-number">{{ match.wins }}</span>
              </td>
              <td class="center">
                <span class="lose-number">{{ match.loses }}</span>
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
            <td>{{ getSeasonName(season.season_id) }}</td>
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
    <div class="section-title">英雄使用统计 (共{{ careerData.hero_stats?.length || 0 }}个英雄)</div>
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
  <div class="loading" v-else-if="loading">
    <div class="loading-spinner"></div>
    <div class="loading-text">正在加载{{ seasonFilterText }}数据...</div>
  </div>

  <!-- 错误状态 -->
  <div class="error-message" v-else-if="error">
    <p>{{ error }}</p>
    <button class="btn btn-primary" @click="loadData">重试</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getCareerData, getSeasonNameMap } from '../api/stats';

const careerData = ref(null);
const seasonFilter = ref('all');
const currentPage = ref(1);
const pageSize = 10;
const loading = ref(false);
const error = ref(null);
const seasonNameMap = ref({});

const playerAvatar = ref('https://hero-wind.oss-cn-shanghai.aliyuncs.com/KPL/KPL_Play_images/KPL2026S1/KSG.无言.png');

const seasonFilterText = computed(() => {
  const map = { all: '全部赛季', league: '联赛', cup: '杯赛' };
  return map[seasonFilter.value];
});

// 加载数据
const loadData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getCareerData(seasonFilter.value);
    careerData.value = res.data.data;
    currentPage.value = 1;
    console.log('数据加载成功', seasonFilter.value, careerData.value);
  } catch (err) {
    console.error('加载失败', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
  }
};

// 加载赛季名称映射
const loadSeasonNameMap = async () => {
  try {
    const res = await getSeasonNameMap();
    seasonNameMap.value = res.data.data || {};
    console.log('赛季名称映射已加载', seasonNameMap.value);
  } catch (err) {
    console.error('加载赛季名称映射失败', err);
    // 使用默认映射作为降级
    seasonNameMap.value = {
      KCC2025: '2025 挑战者杯',
      KPL2026S1: '2026 年春季赛',
    };
  }
};

// 筛选赛季类型
const filterSeasonType = async (type) => {
  if (type === seasonFilter.value) return;
  seasonFilter.value = type;
  await loadData();
};

const getSeasonName = (seasonId) => {
  // 优先使用动态获取的赛季名称映射
  if (seasonNameMap.value[seasonId]) {
    return seasonNameMap.value[seasonId];
  }
  // 降级处理：如果没有映射，返回原始 ID 或默认名称
  const defaultMap = {
    KCC2025: '2025 挑战者杯',
    KPL2026S1: '2026 年春季赛',
  };
  return defaultMap[seasonId] || seasonId;
};

// 筛选后的比赛详情
const filteredMatchDetails = computed(() => {
  if (!careerData.value) return [];
  const matches = careerData.value.match_details || [];
  // 数据已经按赛季类型从 API 获取，不需要再过滤
  return matches;
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
  // 数据已经按赛季类型从 API 获取，直接返回
  return careerData.value.season_stats || [];
});

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
  // 可以根据英雄名字映射到具体的头像 URL
  return '';
};

const getSeasonSummary = () => {
  if (!careerData.value) return '-';
  const total = careerData.value.season_stats?.length || 0;
  if (seasonFilter.value !== 'all') {
    return `${total} 个${seasonFilter.value === 'league' ? '联赛' : '杯赛'}赛季`;
  }
  // 这里可以根据实际情况计算联赛和杯赛的数量
  return `${total} 个赛季`;
};

onMounted(() => {
  loadSeasonNameMap();
  loadData();
});
</script>
