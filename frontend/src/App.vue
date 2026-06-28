<template>
  <div class="app-wrapper">
    <nav class="main-nav">
      <div class="nav-content">
        <div class="nav-header">
          <h1 class="nav-title">KPL选手数据 - 无言</h1>
          <button
            class="nav-toggle"
            @click="menuOpen = !menuOpen"
            :class="{ open: menuOpen }"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
        <div class="nav-links" :class="{ show: menuOpen }">
          <router-link to="/" class="nav-link" @click="menuOpen = false"
            >生涯数据</router-link
          >
          <router-link to="/records" class="nav-link" @click="menuOpen = false"
            >比赛记录</router-link
          >
          <router-link
            to="/abilities"
            class="nav-link"
            @click="menuOpen = false"
            >能力画像</router-link
          >
          <router-link to="/ranking" class="nav-link" @click="menuOpen = false"
            >联盟排名</router-link
          >
          <router-link to="/heroes" class="nav-link" @click="menuOpen = false"
            >英雄池</router-link
          >
          <router-link to="/win-lose" class="nav-link" @click="menuOpen = false"
            >胜负对比</router-link
          >
          <router-link
            to="/ai-analysis"
            class="nav-link"
            @click="menuOpen = false"
            >AI 分析</router-link
          >
          <div class="nav-season" v-if="isShowSeasonSelector">
            <SeasonSelector />
          </div>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="app-footer">
      <div class="footer-content">
        <p class="disclaimer">
          ⚠️ 免责声明：本站数据来源于 KPL
          官方平台，仅作收集与展示，不提供勘误服务。所有数据仅供参考，如有疑问，请以
          KPL 官方发布内容为准。
        </p>
        <p class="footer-text">© 2026 KPL 无言数据站 · 用数据记录成长</p>
      </div>
    </footer>

    <BackToTop />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import BackToTop from './components/BackToTop.vue';
import SeasonSelector from './components/SeasonSelector.vue';

const menuOpen = ref(false);
const route = useRoute();

const isShowSeasonSelector = ref(false);

// 显示赛季选择器的路由
const showSeasonPath = [
  '/abilities',
  '/ranking',
  '/heroes',
  '/win-lose',
  '/ai-analysis',
];

// 路由切换时关闭菜单
watch(
  () => route.path,
  () => {
    menuOpen.value = false;

    // 根据路由显示赛季选择器
    if (showSeasonPath.includes(route.path)) {
      isShowSeasonSelector.value = true;
    } else {
      isShowSeasonSelector.value = false;
    }
  },
);
</script>

<style>
.nav-season {
  display: flex;
  align-items: center;
  margin-left: 8px;
  padding-left: 12px;
  border-left: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
}

@media (max-width: 768px) {
  .nav-season {
    margin-left: 0;
    padding-left: 0;
    border-left: none;
    padding: 6px 0;
  }
}
</style>
