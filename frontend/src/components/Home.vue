<template>
  <div class="container" v-if="careerData">
    <!-- 选手信息 -->
    <div class="player-card">
      <div class="player-header">
        <h2>{{ careerData.player_info.latest_nickname }}</h2>
        <span class="team">{{ careerData.player_info.latest_team }}</span>
        <span class="real-name">（{{ careerData.player_info.real_name }}）</span>
      </div>
      <div class="career-info">
        <p>职业生涯：{{ careerData.career_summary.date_range }}</p>
        <p>
          总比赛：{{ careerData.career_summary.total_matches }}场 | 胜率：{{
            careerData.career_summary.match_win_rate
          }}
          | KDA：{{ careerData.career_summary.kda_ratio }}
        </p>
        <p>
          总击杀/死亡/助攻：{{ careerData.career_summary.total_kills }}/{{ careerData.career_summary.total_deaths }}/{{
            careerData.career_summary.total_assists
          }}
        </p>
      </div>
    </div>

    <!-- 战队统计 -->
    <div class="stats-section">
      <h3>战队数据</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>战队</th>
            <th>对局数</th>
            <th>胜局</th>
            <th>败局</th>
            <th>胜率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in careerData.team_stats" :key="team.team_name">
            <td>{{ team.team_name }}</td>
            <td>{{ team.battles }}</td>
            <td>{{ team.wins }}</td>
            <td>{{ team.loses }}</td>
            <td>{{ team.win_rate }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 赛季统计 -->
    <div class="stats-section">
      <h3>赛季数据</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>赛季</th>
            <th>对局数</th>
            <th>胜局</th>
            <th>败局</th>
            <th>胜率</th>
            <th>KDA</th>
            <th>MVP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="season in careerData.season_stats" :key="season.season_id">
            <td>{{ season.season_id }}</td>
            <td>{{ season.battles }}</td>
            <td>{{ season.wins }}</td>
            <td>{{ season.loses }}</td>
            <td>{{ season.win_rate }}</td>
            <td>{{ season.kda_ratio }}</td>
            <td>{{ season.mvp }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 英雄使用统计 -->
    <div class="stats-section">
      <h3>英雄使用统计（共{{ careerData.hero_stats.length }}个英雄）</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>英雄</th>
            <th>对局数</th>
            <th>胜局</th>
            <th>败局</th>
            <th>胜率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="hero in careerData.hero_stats" :key="hero.hero_id">
            <td>{{ hero.hero_name }}</td>
            <td>{{ hero.battles }}</td>
            <td>{{ hero.wins }}</td>
            <td>{{ hero.loses }}</td>
            <td>{{ hero.win_rate }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 最近比赛（只显示最近 5 场） -->
    <div class="stats-section">
      <h3>最近比赛</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>日期</th>
            <th>对阵</th>
            <th>比分</th>
            <th>结果</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="match in recentMatches" :key="match.match_id">
            <td>{{ match.match_date }}</td>
            <td>{{ match.team_name }} vs {{ match.opponent_team_name }}</td>
            <td>{{ match.match_score }}</td>
            <td :class="match.match_is_win ? 'win' : 'lose'">
              {{ match.match_is_win ? '胜利' : '失败' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const careerData = ref(null);

// 计算最近 5 场比赛
const recentMatches = computed(() => {
  if (!careerData.value) return [];
  return careerData.value.match_details.slice(0, 5);
});

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
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.player-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 30px;
}

.player-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.player-header h2 {
  margin: 0;
  font-size: 28px;
}

.team {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.real-name {
  font-size: 14px;
  opacity: 0.9;
}

.career-info p {
  margin: 8px 0;
  font-size: 14px;
}

.stats-section {
  margin-bottom: 40px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stats-section h3 {
  padding: 20px 20px 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  border-bottom: 1px solid #eee;
  padding: 12px 16px;
  text-align: left;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
}

.data-table tr:hover {
  background: #fafafa;
}

.win {
  color: #52c41a;
  font-weight: 500;
}

.lose {
  color: #ff4d4f;
}

@media (max-width: 768px) {
  .container {
    padding: 12px;
  }

  .data-table {
    font-size: 12px;
  }

  .data-table th,
  .data-table td {
    padding: 8px 10px;
  }
}
</style>
