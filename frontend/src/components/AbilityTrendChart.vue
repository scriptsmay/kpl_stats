<template>
  <div class="ability-trend-chart">
    <!-- 控制栏 -->
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <!-- 时间范围 -->
        <div class="btn-group">
          <button
            v-for="r in timeRanges"
            :key="r.key"
            class="range-btn"
            :class="{ active: timeRange === r.key }"
            @click="timeRange = r.key"
          >{{ r.label }}</button>
        </div>

        <!-- 图表模式 -->
        <div class="btn-group">
          <button
            class="range-btn"
            :class="{ active: chartMode === 'line' }"
            @click="chartMode = 'line'"
            title="折线图"
          >📈 折线</button>
          <button
            class="range-btn"
            :class="{ active: chartMode === 'step' }"
            @click="chartMode = 'step'"
            title="阶梯图"
          >📊 阶梯</button>
        </div>

        <!-- 值/Delta 模式切换 -->
        <div class="btn-group">
          <button
            class="range-btn"
            :class="{ active: displayMode === 'value' }"
            @click="displayMode = 'value'"
            title="显示原始数值"
          >📏 值模式</button>
          <button
            class="range-btn"
            :class="{ active: displayMode === 'delta' }"
            @click="displayMode = 'delta'"
            title="显示相对起点的变化量"
          >📊 Delta</button>
        </div>
      </div>

      <div class="toolbar-right">
        <!-- 滞后提示 -->
        <div class="lag-alert" v-if="lagStatus" :class="lagStatus.type">
          <span class="lag-icon">{{ lagStatus.type === 'pending' ? '⏳' : '✅' }}</span>
          <span class="lag-text">{{ lagStatus.text }}</span>
        </div>
      </div>
    </div>

    <!-- 维度选择器 -->
    <div class="dim-selector-bar">
      <div class="dim-chips">
        <button
          v-for="dim in abilityDims"
          :key="dim.key"
          class="dim-chip"
          :class="{ active: selectedDims.includes(dim.key) }"
          :style="chipStyle(dim.key)"
          @click="toggleDim(dim.key)"
        >{{ dim.label }}</button>
      </div>
      <div class="dim-hint" v-if="selectedDims.length >= 6">⚠️ 维度较多，建议切换 Delta 模式对比趋势</div>
    </div>

    <!-- 图表区 -->
    <div class="chart-container">
      <div v-if="loading" class="chart-loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">加载中...</div>
      </div>
      <div v-else-if="error" class="chart-error">
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="reload">重试</button>
      </div>
      <canvas v-else ref="chartCanvas"></canvas>
    </div>

    <!-- 关键节点 -->
    <div class="key-nodes" v-if="visibleKeyNodes.length && !loading && !error">
      <div class="section-label">🔍 关键节点</div>
      <div class="node-list">
        <div
          v-for="(node, idx) in visibleKeyNodes"
          :key="idx"
          class="node-item"
          :style="{ borderColor: node.color }"
        >
          <span class="node-title" :style="{ color: node.color }">{{ node.title }}</span>
          <span class="node-detail">{{ node.detail }}</span>
          <span class="node-date" v-if="filteredData[node.index]">
            {{ formatDate(filteredData[node.index].x_axis_ts) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 变化统计 -->
    <div class="change-stats" v-if="changeStats && !loading && !error">
      <div class="section-label">📊 变化统计<span class="stats-range" v-if="filteredData.length >= 2">
        （{{ formatDate(filteredData[0].x_axis_ts) }} → {{ formatDate(filteredData[filteredData.length - 1].x_axis_ts) }}）
      </span></div>
      <div class="stats-grid">
        <div
          v-for="dim in selectedDimsInfo"
          :key="dim.key"
          class="stat-card"
        >
          <div class="stat-dim-label" :style="{ color: dim.color }">{{ dim.label }}</div>
          <div class="stat-values">
            <span class="stat-first">{{ formatVal(changeStats[dim.key]?.first) }}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-last">{{ formatVal(changeStats[dim.key]?.last) }}</span>
          </div>
          <div
            class="stat-delta"
            :class="(changeStats[dim.key]?.delta || 0) >= 0 ? 'up' : 'down'"
          >
            {{ (changeStats[dim.key]?.delta || 0) >= 0 ? '+' : '' }}{{ formatVal(changeStats[dim.key]?.delta) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="data-table-section" v-if="showTable && filteredData.length && !loading && !error">
      <div class="section-label">📋 数据明细</div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>对手</th>
              <th>比分</th>
              <th>累计局数</th>
              <th v-for="dim in selectedDimsInfo" :key="dim.key">{{ dim.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(snapshot, idx) in filteredData" :key="idx">
              <td>{{ formatDate(snapshot.x_axis_ts) }}</td>
              <td>{{ snapshot.aligned_match?.opponent || '-' }}</td>
              <td :class="snapshot.aligned_match?.is_win ? 'win' : (snapshot.aligned_match ? 'lose' : '')">
                {{ snapshot.aligned_match?.score || '-' }}
              </td>
              <td>{{ snapshot.total_matches }}</td>
              <td v-for="dim in selectedDimsInfo" :key="dim.key">
                {{ formatVal(getDimValue(snapshot, dim.key)) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 表格切换按钮 -->
    <button class="table-toggle" v-if="!loading && !error && filteredData.length" @click="showTable = !showTable">
      {{ showTable ? '▲ 收起数据表格' : '▼ 展开数据表格' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Chart, registerables } from 'chart.js';
import { useAbilityTrend, ABILITY_DIMS, TIME_RANGES } from '../composables/useAbilityTrend.js';

Chart.register(...registerables);

const DIM_COLORS = [
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#10b981', // emerald
  '#8b5cf6', // violet
  '#ef4444', // red
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#84cc16', // lime
  '#f97316', // orange
  '#6366f1', // indigo
  '#14b8a6', // teal
  '#a855f7', // purple
  '#eab308', // yellow
  '#64748b', // slate
];

const props = defineProps({
  seasonId: { type: String, required: true },
});

const chartCanvas = ref(null);
let chartInstance = null;

const selectedDims = ref(['overall_rating']);
const chartMode = ref('line');
const displayMode = ref('value'); // 'value' | 'delta' — 用户手动切换
const showTable = ref(false);
const abilityDims = ABILITY_DIMS;
const timeRanges = TIME_RANGES;

const {
  filteredData,
  positionAverages,
  keyNodes,
  lagStatus,
  changeStats,
  timeRange,
  loading,
  error,
  loadData,
} = useAbilityTrend(computed(() => props.seasonId));

// ─── 维度选择 ─────────────────────────────────────────

const selectedDimsInfo = computed(() => {
  return selectedDims.value.map((key, idx) => {
    const dim = ABILITY_DIMS.find((d) => d.key === key);
    return { ...dim, color: DIM_COLORS[idx % DIM_COLORS.length] };
  });
});

function toggleDim(key) {
  const idx = selectedDims.value.indexOf(key);
  if (idx >= 0) {
    if (selectedDims.value.length > 1) selectedDims.value.splice(idx, 1);
  } else {
    selectedDims.value.push(key);
  }
}

function chipStyle(key) {
  const idx = selectedDims.value.indexOf(key);
  if (idx < 0) return {};
  return {
    backgroundColor: DIM_COLORS[idx % DIM_COLORS.length] + '20',
    borderColor: DIM_COLORS[idx % DIM_COLORS.length],
    color: DIM_COLORS[idx % DIM_COLORS.length],
  };
}

// ─── Y 轴模式 ──────────────────────────────────────────

const yAxisMode = computed(() => {
  if (displayMode.value === 'delta') return 'delta';
  // 值模式：2 维度用双 Y 轴，其余用单 Y 轴
  if (selectedDims.value.length === 2) return 'dual';
  return 'single';
});

// ─── 可见关键节点 ──────────────────────────────────────

const visibleKeyNodes = computed(() => {
  if (!filteredData.value || !filteredData.value.length || !keyNodes.value.length) return [];
  const minTs = filteredData.value[0].x_axis_ts;
  const maxTs = filteredData.value[filteredData.value.length - 1].x_axis_ts;
  return keyNodes.value.filter((n) => {
    const nodeTs = filteredData.value[n.index]?.x_axis_ts;
    return nodeTs != null && nodeTs >= minTs && nodeTs <= maxTs;
  });
});

// ─── 工具函数 ──────────────────────────────────────────

function getDimValue(snapshot, dimKey) {
  if (dimKey === 'overall_rating') return snapshot.overall_rating;
  return snapshot.abilities?.[dimKey];
}

function formatDate(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function formatVal(v) {
  if (v == null) return '-';
  return Math.round(v * 10) / 10;
}

// ─── 图表构建 ──────────────────────────────────────────

function buildDatasets() {
  const data = filteredData.value;
  if (!data.length) return { datasets: [], labels: [] };

  const labels = data.map((s) => formatDate(s.x_axis_ts));
  const isStep = chartMode.value === 'step';
  const isDelta = yAxisMode.value === 'delta';
  const isDual = yAxisMode.value === 'dual';

  const datasets = selectedDimsInfo.value.map((dim, idx) => {
    let values;
    if (isDelta) {
      // Delta 模式：展示相对第一个数据点的变化量
      const baseVal = getDimValue(data[0], dim.key);
      values = data.map((s) => {
        const v = getDimValue(s, dim.key);
        return v != null && baseVal != null ? Math.round((v - baseVal) * 10) / 10 : null;
      });
    } else {
      values = data.map((s) => getDimValue(s, dim.key));
    }

    const pointColors = data.map((s) => {
      // 中国电竞惯例：胜=红、负=绿
      if (s.aligned_match) return s.aligned_match.is_win ? 'rgba(239, 68, 68, 1)' : 'rgba(34, 197, 94, 1)';
      return 'rgba(156, 163, 175, 1)';
    });

    return {
      label: dim.label,
      data: values,
      borderColor: dim.color,
      backgroundColor: dim.color + '15',
      fill: idx === 0 && !isDelta,
      tension: isStep ? 0 : 0.3,
      stepped: isStep ? 'before' : false,
      pointRadius: 5,
      pointHoverRadius: 8,
      pointBackgroundColor: pointColors,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      yAxisID: isDual ? (idx === 0 ? 'y' : 'y1') : 'y',
    };
  });

  // 同位置平均虚线（仅单维度且非 Delta 模式时显示）
  if (selectedDims.value.length === 1 && !isDelta && positionAverages.value) {
    const dimKey = selectedDims.value[0];
    const avgVal = positionAverages.value[dimKey];
    if (avgVal != null) {
      datasets.push({
        label: '同位置平均',
        data: data.map(() => avgVal),
        borderColor: 'rgba(156, 163, 175, 0.6)',
        borderDash: [6, 4],
        borderWidth: 1.5,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
        yAxisID: 'y',
      });
    }
  }

  return { datasets, labels };
}

function updateChart() {
  if (!chartCanvas.value || !filteredData.value || !filteredData.value.length) return;

  const ctx = chartCanvas.value.getContext('2d');
  const { datasets, labels } = buildDatasets();
  const isDual = yAxisMode.value === 'dual';
  const isDelta = yAxisMode.value === 'delta';

  if (chartInstance) chartInstance.destroy();

  const scalesConfig = {
    x: {
      grid: { display: false },
      ticks: { maxRotation: 45, minRotation: 45, font: { size: 11 } },
    },
  };

  if (isDelta) {
    scalesConfig.y = {
      grid: { color: 'rgba(156, 163, 175, 0.1)' },
      ticks: {
        font: { size: 11 },
        callback: (v) => (v >= 0 ? `+${v}` : v),
      },
      title: { display: true, text: '变化量 (Δ)', font: { size: 12 } },
    };
  } else if (isDual) {
    scalesConfig.y = {
      type: 'linear',
      position: 'left',
      grid: { color: 'rgba(156, 163, 175, 0.1)' },
      title: { display: true, text: selectedDimsInfo.value[0]?.label, font: { size: 12 } },
    };
    scalesConfig.y1 = {
      type: 'linear',
      position: 'right',
      grid: { drawOnChartArea: false },
      title: { display: true, text: selectedDimsInfo.value[1]?.label, font: { size: 12 } },
    };
  } else {
    scalesConfig.y = {
      grid: { color: 'rgba(156, 163, 175, 0.1)' },
      ticks: { font: { size: 11 } },
    };
  }

  const data = filteredData.value;

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: selectedDims.value.length > 1 || yAxisMode.value === 'single',
          position: 'top',
          // 用矩形色块读 dataset.borderColor，避免 usePointStyle+circle 读到 pointBackgroundColor 数组
          // （pointBackgroundColor 是按数据点胜负着色的，legend 只取首元素会全部显示为红色）
          labels: {
            font: { size: 12 },
            usePointStyle: false,
            boxWidth: 16,
            boxHeight: 3,
            padding: 12,
          },
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#fff',
          bodyColor: '#e5e7eb',
          borderColor: 'rgba(75, 85, 99, 0.5)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            title: function (items) {
              const idx = items[0].dataIndex;
              const snapshot = data[idx];
              if (snapshot?.aligned_match) {
                const m = snapshot.aligned_match;
                return `⚔️ vs ${m.opponent} (${m.score})${m.is_win ? ' 胜' : ' 负'}`;
              }
              return `📅 ${items[0].label}`;
            },
            label: function (item) {
              const val = Math.round(item.raw * 10) / 10;
              const prefix = isDelta ? 'Δ ' : '';
              return `${prefix}${item.dataset.label}: ${val >= 0 && isDelta ? '+' : ''}${val}`;
            },
            // 色块用 dataset 折线颜色（borderColor），避免读到 pointBackgroundColor 数组
            // （pointBackgroundColor 按数据点胜负着色，hover 时所有指标行会一起变红/绿，无法区分各线）
            labelColor: function (ctx) {
              const color = ctx.dataset.borderColor || '#9ca3af';
              return {
                borderColor: color,
                backgroundColor: color,
                borderWidth: 0,
                borderRadius: 2,
              };
            },
            afterBody: function (items) {
              const idx = items[0].dataIndex;
              const snapshot = data[idx];
              const lines = [];
              if (snapshot?.aligned_match) {
                lines.push('');
                lines.push(`📍 ${snapshot.aligned_match.stage || ''}`);
                lines.push(`🎮 累计 ${snapshot.total_matches} 局`);
                // 显示比赛日期（来自赛程，"MM-DD HH:mm" 格式）
                if (snapshot.aligned_match.date) {
                  lines.push(`🕐 比赛: ${snapshot.aligned_match.date}`);
                }
              } else if (snapshot) {
                // 降级兜底（对齐误差>2 局）：能力值仍源于最近一场比赛
                lines.push('');
                lines.push('ℹ️ 对齐误差较大，使用数据更新日期兜底');
                if (snapshot.last_updated) {
                  lines.push(`🕐 数据更新: ${snapshot.last_updated}`);
                }
              }
              return lines;
            },
          },
        },
      },
      scales: scalesConfig,
    },
  });
}

function reload() {
  loadData();
}

// ─── 生命周期 ──────────────────────────────────────────

watch(
  [filteredData, selectedDims, chartMode, displayMode, timeRange, positionAverages],
  () => {
    if (filteredData.value && filteredData.value.length) {
      nextTick(() => updateChart());
    }
  },
  { deep: true },
);

onMounted(() => {
  nextTick(() => {
    if (filteredData.value && filteredData.value.length) updateChart();
  });
});

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
});
</script>

<style scoped>
.ability-trend-chart {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* ─── 工具栏 ─── */
.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-group {
  display: flex;
  gap: 2px;
  padding: 3px;
  background: var(--gray-100, #f3f4f6);
  border-radius: 8px;
}

.range-btn {
  padding: 5px 12px;
  border: none;
  background: transparent;
  color: var(--gray-600, #6b7280);
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.range-btn:hover {
  color: var(--gray-800, #374151);
}

.range-btn.active {
  background: var(--bg-card, #fff);
  color: var(--gray-900, #111827);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.lag-alert {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.lag-alert.pending {
  background: rgba(251, 191, 36, 0.1);
  color: #b45309;
}

.lag-alert.complete {
  background: rgba(34, 197, 94, 0.1);
  color: #15803d;
}

/* ─── 维度选择 ─── */
.dim-selector-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.dim-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.dim-chip {
  padding: 4px 12px;
  border: 1.5px solid var(--gray-200, #e5e7eb);
  background: transparent;
  color: var(--gray-500, #6b7280);
  font-size: 13px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.15s;
}

.dim-chip:hover {
  border-color: var(--gray-400, #9ca3af);
}

.dim-chip.active {
  font-weight: 600;
}

.dim-hint {
  font-size: 12px;
  color: #b45309;
  background: rgba(251, 191, 36, 0.1);
  padding: 3px 10px;
  border-radius: 6px;
}

/* ─── 图表 ─── */
.chart-container {
  position: relative;
  height: 380px;
}

.chart-loading,
.chart-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary, #6b7280);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color, #e5e7eb);
  border-top-color: var(--primary-color, #3b82f6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.loading-text { font-size: 14px; }
.chart-error p { margin: 0; font-size: 14px; }

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-primary {
  background: var(--primary-color, #3b82f6);
  color: #fff;
}

/* ─── 关键节点 ─── */
.key-nodes {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-100, #f3f4f6);
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700, #374151);
  margin-bottom: 10px;
}

.stats-range {
  font-weight: 400;
  font-size: 12px;
  color: var(--gray-500, #6b7280);
}

.node-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-left: 3px solid;
  background: var(--gray-50, #f9fafb);
  border-radius: 4px;
  font-size: 13px;
}

.node-title { font-weight: 600; }
.node-detail { color: var(--gray-500, #6b7280); }
.node-date { color: var(--gray-400, #9ca3af); font-size: 12px; }

/* ─── 变化统计 ─── */
.change-stats {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-100, #f3f4f6);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 12px;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 8px;
  text-align: center;
}

.stat-dim-label {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.stat-values {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800, #1f2937);
  margin-bottom: 4px;
}

.stat-arrow { color: var(--gray-400, #9ca3af); font-size: 14px; }

.stat-delta {
  font-size: 14px;
  font-weight: 700;
}

/* 中国电竞惯例：涨=红、跌=绿 */
.stat-delta.up { color: #dc2626; }
.stat-delta.down { color: #15803d; }

/* ─── 数据表格 ─── */
.data-table-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-100, #f3f4f6);
}

.table-wrap {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--gray-200, #e5e7eb);
  border-radius: 8px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table thead {
  position: sticky;
  top: 0;
  background: var(--gray-50, #f9fafb);
  z-index: 1;
}

.data-table th,
.data-table td {
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid var(--gray-100, #f3f4f6);
  white-space: nowrap;
}

.data-table th {
  font-weight: 600;
  color: var(--gray-600, #6b7280);
}

.data-table td.win { color: #dc2626; font-weight: 600; }
.data-table td.lose { color: #15803d; font-weight: 600; }

.data-table tbody tr:hover {
  background: var(--gray-50, #f9fafb);
}

.table-toggle {
  margin-top: 12px;
  width: 100%;
  padding: 8px;
  border: 1px dashed var(--gray-300, #d1d5db);
  background: transparent;
  color: var(--gray-500, #6b7280);
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.table-toggle:hover {
  border-color: var(--gray-400, #9ca3af);
  color: var(--gray-700, #374151);
}

@media (max-width: 768px) {
  .chart-toolbar { flex-direction: column; align-items: flex-start; }
  .chart-container { height: 300px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .dim-chips { gap: 4px; }
  .dim-chip { font-size: 12px; padding: 3px 8px; }
}
</style>
