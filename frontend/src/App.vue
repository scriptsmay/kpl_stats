<template>
  <div class="app-wrapper">
    <nav class="main-nav">
      <div class="nav-content">
        <h1 class="nav-title">KPL 选手数据</h1>
        <div class="nav-links">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/admin" class="nav-link admin-link">数据管理</router-link>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-wrapper {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%);
  min-height: 100vh;
  padding: 20px;
}

.main-nav {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  padding: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 20px 20px 0 0;
  max-width: 1400px;
  margin: 0 auto;
}

.nav-content {
  max-width: 1400px;
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
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
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
  max-width: 1400px;
  margin: 0 auto;
}

.main-content > * {
  background: #fff;
  border-radius: 0 0 20px 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .app-wrapper {
    padding: 10px;
    border-radius: 10px;
  }

  .main-nav {
    border-radius: 10px 10px 0 0;
    padding: 12px 0;
  }

  .nav-content {
    padding: 0 15px;
  }

  .nav-title {
    font-size: 18px;
  }

  .nav-link {
    padding: 6px 12px;
    font-size: 13px;
  }

  .main-content > * {
    border-radius: 0 0 10px 10px;
  }
}
</style>
