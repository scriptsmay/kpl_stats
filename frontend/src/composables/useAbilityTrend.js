import { ref, computed, watch } from 'vue';
import { getAbilityTimeline, getSchedule } from '../api/github-data.js';

export const ABILITY_DIMS = [
  { key: 'overall_rating', label: '综合评分', isOverall: true },
  { key: 'damage_output', label: '输出能力' },
  { key: 'teamfight', label: '团战能力' },
  { key: 'initiation', label: '开团能力' },
  { key: 'early_game', label: '前期能力' },
  { key: 'mid_game', label: '中期能力' },
  { key: 'late_game', label: '后期能力' },
  { key: 'map_control', label: '控图能力' },
  { key: 'invasion_ability', label: '入侵能力' },
  { key: 'support_ability', label: '辅助能力' },
  { key: 'economy', label: '经济能力' },
  { key: 'tankiness', label: '承伤能力' },
  { key: 'durability', label: '续航能力' },
];

export const TIME_RANGES = [
  { key: '7d', label: '近7天', days: 7 },
  { key: '14d', label: '近14天', days: 14 },
  { key: '30d', label: '近30天', days: 30 },
  { key: 'all', label: '全部', days: 0 },
];

// ─── 赛程累计对局序列 ───────────────────────────────────────

function buildMatchCumulative(scheduleData) {
  const matches = Array.isArray(scheduleData)
    ? scheduleData
    : scheduleData?.matches || scheduleData?.data || [];

  if (!Array.isArray(matches)) return [];

  return matches
    .filter((m) => m.status === 4 || m.status === 'finished')
    .sort((a, b) => (a.start_ts || 0) - (b.start_ts || 0))
    .map((match) => {
      // KSG 可能是 team_a 或 team_b，用 === 'KSG' 精确匹配
      const isKsgHome = match.team_a === 'KSG';
      const isKsgAway = match.team_b === 'KSG';
      const ksgScore = isKsgHome
        ? Number(match.score_a)
        : isKsgAway
          ? Number(match.score_b)
          : 0;
      const oppScore = isKsgHome
        ? Number(match.score_b)
        : isKsgAway
          ? Number(match.score_a)
          : 0;
      const opponent = isKsgHome ? match.team_b : match.team_a;
      const gameCount = ksgScore + oppScore;

      return {
        match_id: match.schedule_id || match.match_id,
        date: match.date,
        start_ts: match.start_ts,
        opponent,
        score: `${ksgScore}:${oppScore}`,
        ksgScore,
        oppScore,
        is_win: ksgScore > oppScore,
        stage: match.stage || '',
        game_count: gameCount,
        cumulative_matches: 0, // 后面填充
      };
    })
    .reduce((acc, match) => {
      // 累计小局数
      const prevTotal = acc.length > 0 ? acc[acc.length - 1].cumulative_matches : 0;
      match.cumulative_matches = prevTotal + match.game_count;
      acc.push(match);
      return acc;
    }, []);
}

// ─── 能力快照对齐到比赛 ─────────────────────────────────────

function alignAbilityToMatch(snapshot, matchCumulative) {
  const totalMatches = Math.round(snapshot.total_matches || 0);
  if (totalMatches <= 0 || !matchCumulative.length) {
    return { ...snapshot, aligned_match: null, x_axis_ts: null, is_game_day: false };
  }

  const matched = matchCumulative.find((m) => m.cumulative_matches >= totalMatches);
  if (matched) {
    const diff = matched.cumulative_matches - totalMatches;
    if (diff > 2) {
      console.warn(
        `[useAbilityTrend] 对齐误差过大: snapshot total_matches=${totalMatches}, ` +
        `nearest match cumulative=${matched.cumulative_matches}, diff=${diff}. ` +
        `降级为 last_updated 日期对齐.`,
      );
      return {
        ...snapshot,
        aligned_match: null,
        x_axis_ts: snapshot.last_updated
          ? new Date(snapshot.last_updated).getTime()
          : new Date(snapshot.date).getTime(),
        is_game_day: false,
        use_fallback_date: true,
      };
    }
    return {
      ...snapshot,
      aligned_match: matched,
      x_axis_ts: matched.start_ts * 1000,
      is_game_day: true,
    };
  }

  const lastMatch = matchCumulative[matchCumulative.length - 1];
  if (totalMatches > lastMatch.cumulative_matches) {
    console.warn(
      `[useAbilityTrend] 快照 total_matches=${totalMatches} 超过赛程累计=${lastMatch.cumulative_matches}`,
    );
  }

  return {
    ...snapshot,
    aligned_match: lastMatch,
    x_axis_ts: lastMatch.start_ts * 1000,
    is_game_day: true,
  };
}

// ─── 去重：同一场比赛的多个快照只保留最后一个 ───────────────

function deduplicateSnapshots(snapshots) {
  const seen = new Map();
  for (const s of snapshots) {
    const key = s.aligned_match ? s.aligned_match.match_id : s.date;
    seen.set(key, s); // 后面的覆盖前面的
  }
  return Array.from(seen.values()).sort((a, b) => a.x_axis_ts - b.x_axis_ts);
}

// ─── 关键节点识别 ───────────────────────────────────────────

function identifyKeyNodes(alignedData) {
  if (!alignedData || alignedData.length < 2) return [];

  const nodes = [];

  for (let i = 1; i < alignedData.length; i++) {
    const prev = alignedData[i - 1];
    const curr = alignedData[i];

    // 排名突变（+/-5名）
    if (prev.overall_rank != null && curr.overall_rank != null) {
      const rankDelta = prev.overall_rank - curr.overall_rank; // 正数=上升
      if (Math.abs(rankDelta) >= 5) {
        nodes.push({
          index: i,
          type: 'rank_shift',
          title: `排名${rankDelta > 0 ? '上升' : '下降'} ${Math.abs(rankDelta)} 名`,
          detail: `#${prev.overall_rank} → #${curr.overall_rank}`,
          color: rankDelta > 0 ? '#dc2626' : '#15803d',
        });
      }
    }

    // 赛段切换
    if (prev.aligned_match?.stage && curr.aligned_match?.stage) {
      if (prev.aligned_match.stage !== curr.aligned_match.stage) {
        nodes.push({
          index: i,
          type: 'stage_change',
          title: `赛段切换`,
          detail: `${curr.aligned_match.stage}`,
          color: '#7c3aed',
        });
      }
    }
  }

  return nodes;
}

// ─── 主 Composable ─────────────────────────────────────────

export function useAbilityTrend(seasonId) {
  if (!seasonId) {
    throw new Error('[useAbilityTrend] seasonId is required');
  }

  const timeline = ref(null);
  const schedule = ref(null);
  const alignedData = ref(null);
  const loading = ref(false);
  const error = ref(null);
  const matchCumulative = ref([]);
  const positionAverages = ref(null);
  const keyNodes = ref([]);
  const timeRange = ref('all');

  // ─── 滞后状态 ─────────────────────────────────────────
  const lagStatus = computed(() => {
    if (!alignedData.value || !matchCumulative.value.length) return null;
    const lastSnapshot = alignedData.value[alignedData.value.length - 1];
    const lastMatch = matchCumulative.value[matchCumulative.value.length - 1];
    if (!lastSnapshot || !lastMatch) return null;

    const snapshotMatches = Math.round(lastSnapshot.total_matches || 0);
    const totalMatches = lastMatch.cumulative_matches;
    const diff = totalMatches - snapshotMatches;

    if (diff <= 0) return { type: 'complete', text: '赛季数据完整', diff: 0 };
    return { type: 'pending', text: `最近 ${diff} 局比赛数据待更新`, diff };
  });

  // ─── 时间范围过滤后的数据 ─────────────────────────────
  const filteredData = computed(() => {
    if (!alignedData.value || !alignedData.value.length) return [];
    if (timeRange.value === 'all') return alignedData.value;

    const rangeConfig = TIME_RANGES.find((r) => r.key === timeRange.value);
    if (!rangeConfig || rangeConfig.days === 0) return alignedData.value;

    const now = Date.now();
    const cutoff = now - rangeConfig.days * 24 * 60 * 60 * 1000;
    return alignedData.value.filter((s) => s.x_axis_ts >= cutoff);
  });

  // ─── 变化统计（首尾对比） ─────────────────────────────
  const changeStats = computed(() => {
    if (!filteredData.value || filteredData.value.length < 2) return null;

    const first = filteredData.value[0];
    const last = filteredData.value[filteredData.value.length - 1];
    const stats = {};

    for (const dim of ABILITY_DIMS) {
      const firstVal = dim.isOverall ? first.overall_rating : first.abilities?.[dim.key];
      const lastVal = dim.isOverall ? last.overall_rating : last.abilities?.[dim.key];
      if (firstVal != null && lastVal != null) {
        const delta = Math.round((lastVal - firstVal) * 10) / 10;
        stats[dim.key] = { first: firstVal, last: lastVal, delta };
      }
    }

    return stats;
  });

  async function loadData() {
    loading.value = true;
    error.value = null;

    try {
      const sid = typeof seasonId === 'object' && seasonId.value ? seasonId.value : seasonId;
      const [timelineData, scheduleData] = await Promise.all([
        getAbilityTimeline(sid),
        getSchedule(sid),
      ]);

      timeline.value = timelineData;
      schedule.value = scheduleData;

      // 提取 position_averages
      positionAverages.value =
        timelineData?.position_averages ||
        timelineData?.data?.position_averages ||
        null;

      // 构建赛程累计序列
      const matches = Array.isArray(scheduleData)
        ? scheduleData
        : scheduleData?.matches || scheduleData?.data || scheduleData?.data?.matches || [];
      matchCumulative.value = buildMatchCumulative(matches);

      // 对齐快照到比赛
      const snapshots = Array.isArray(timelineData)
        ? timelineData
        : timelineData?.snapshots || timelineData?.data?.snapshots || [];

      const aligned = snapshots
        .filter((s) => Math.round(s.total_matches || 0) > 0)
        .map((s) => alignAbilityToMatch(s, matchCumulative.value))
        .filter((s) => s.x_axis_ts)
        .sort((a, b) => a.x_axis_ts - b.x_axis_ts);

      alignedData.value = deduplicateSnapshots(aligned);
      keyNodes.value = identifyKeyNodes(alignedData.value);
    } catch (err) {
      error.value = err.message;
      console.error('[useAbilityTrend] 加载数据失败:', err);
    } finally {
      loading.value = false;
    }
  }

  // ─── 赛季切换时清空旧数据重新加载 ─────────────────────
  if (typeof seasonId === 'object' && seasonId.value !== undefined) {
    watch(seasonId, () => {
      alignedData.value = null;
      timeline.value = null;
      schedule.value = null;
      matchCumulative.value = [];
      positionAverages.value = null;
      keyNodes.value = [];
      loadData();
    });
  }

  loadData();

  return {
    timeline,
    schedule,
    alignedData,
    filteredData,
    matchCumulative,
    positionAverages,
    keyNodes,
    lagStatus,
    changeStats,
    timeRange,
    loading,
    error,
    loadData,
    ABILITY_DIMS,
    TIME_RANGES,
  };
}
