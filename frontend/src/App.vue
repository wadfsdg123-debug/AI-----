<template>
  <div id="app">
    <!-- 扫描线效果 -->
    <div class="scanline"></div>
    
    <!-- 导航 -->
    <nav class="cyber-nav">
      <h1 class="glitch" data-text="CODE AUDIT SYSTEM">CODE AUDIT SYSTEM</h1>
      <div class="nav-links">
        <router-link to="/" class="cyber-link">上传</router-link>
        <router-link to="/dashboard" class="cyber-link">仪表盘</router-link>
      </div>
    </nav>
    
    <!-- 页面内容 -->
    <router-view></router-view>
  </div>
</template>

<style>
.cyber-nav {
  background: var(--bg-card);
  border-bottom: 2px solid var(--primary);
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 0 20px var(--primary-glow);
}

.cyber-nav h1 {
  margin: 0;
  font-size: 24px;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.cyber-link {
  color: var(--text);
  text-decoration: none;
  padding: 8px 16px;
  border: 1px solid transparent;
  transition: all 0.3s;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.cyber-link:hover,
.cyber-link.router-link-active {
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: 0 0 10px var(--primary-glow);
}
</style>