<template>
  <div id="app">
    <!-- 导航菜单（可选） -->
    <nav class="nav-menu">
      <router-link to="/">上传</router-link>
      <router-link to="/dashboard">仪表盘</router-link>
    </nav>
    
    <!-- 关键：必须有这个路由出口 -->
    <router-view></router-view>
  </div>
</template>

<style>
.nav-menu {
  padding: 16px;
  background: #f5f7fa;
  margin-bottom: 20px;
}

.nav-menu a {
  margin-right: 16px;
  color: #606266;
  text-decoration: none;
}

.nav-menu a.router-link-active {
  color: #409eff;
  font-weight: bold;
}
</style>