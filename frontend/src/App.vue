<template>
  <div class="app-wrapper">
    <nav class="main-nav">
      <div class="nav-content">
        <h1 class="nav-title">KPL选手数据 - 无言（赵昊宇）</h1>
        <div class="nav-links">
          <router-link to="/" class="nav-link">生涯数据</router-link>
          <router-link to="/records" class="nav-link">比赛记录</router-link>
          <router-link to="/admin" class="nav-link admin-link hide">数据管理</router-link>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="app-footer">
      <div class="footer-content">
        <p class="disclaimer">
          ⚠️ 免责声明：所有数据均由 KPL 官方数据平台提供，本站只做收集与展示，不zuo勘误。
          数据仅供参考，如有异议请以 KPL 官方数据为准。
        </p>
        <p class="footer-text">
          © 2026 KPL 无言数据站 · 用数据记录成长
        </p>
      </div>
    </footer>

    <BackToTop />
  </div>
</template>

<script setup>
import BackToTop from './components/BackToTop.vue';
</script>
