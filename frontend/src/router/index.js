import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue')
  },
  {
    path: '/audit/:id',  // 关键：必须有 :id 参数
    name: 'Audit',
    component: () => import('../views/AuditView.vue')
  },
  {
    path: '/terminal',   // 如果有单独的终端页面
    name: 'Terminal',
    component: () => import('../views/Terminal.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router