<template>
  <div class="app-wrapper">
    <nav class="main-nav">
      <div class="nav-content">
        <h1 class="nav-title">KPL 选手数据</h1>
        <!-- <div class="nav-links">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/admin" class="nav-link admin-link">数据管理</router-link>
        </div> -->
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup></script>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.main-nav {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-title {
  margin: 0;
  font-size: 20px;
  color: white;
  font-weight: 600;
}

.nav-links {
  display: flex;
  gap: 16px;
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s;
  font-size: 14px;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.3);
  color: white;
  font-weight: 500;
}

.admin-link {
  background: rgba(255, 255, 255, 0.2);
}

.main-content {
  padding: 20px;
}
</style>
