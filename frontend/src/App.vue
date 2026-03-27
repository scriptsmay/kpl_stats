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
  </div>
</template>

<script setup></script>
