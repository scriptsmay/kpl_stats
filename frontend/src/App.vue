<template>
  <div class="app-wrapper">
    <nav class="main-nav">
      <div class="nav-content">
        <div class="nav-header">
          <h1 class="nav-title">KPL选手数据 - 无言</h1>
          <button class="nav-toggle" @click="menuOpen = !menuOpen" :class="{ open: menuOpen }">
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
        <div class="nav-links" :class="{ show: menuOpen }">
          <router-link to="/" class="nav-link" @click="menuOpen = false">生涯数据</router-link>
          <router-link to="/abilities" class="nav-link" @click="menuOpen = false">能力画像</router-link>
          <router-link to="/ranking" class="nav-link" @click="menuOpen = false">联盟排名</router-link>
          <router-link to="/heroes" class="nav-link" @click="menuOpen = false">英雄池</router-link>
          <router-link to="/win-lose" class="nav-link" @click="menuOpen = false">胜负对比</router-link>
          <router-link to="/records" class="nav-link" @click="menuOpen = false">比赛记录</router-link>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="app-footer">
      <div class="footer-content">
        <p class="disclaimer">
          ⚠️ 免责声明：本站数据来源于 KPL 官方平台，仅作收集与展示，不提供勘误服务。所有数据仅供参考，如有疑问，请以 KPL
          官方发布内容为准。
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

const menuOpen = ref(false);
const route = useRoute();

// 路由切换时关闭菜单
watch(() => route.path, () => { menuOpen.value = false; });
</script>
