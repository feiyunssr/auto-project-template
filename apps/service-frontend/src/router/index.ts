import { createRouter, createWebHistory } from 'vue-router'

import DashboardPage from '../pages/DashboardPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ProfilesPage from '../pages/ProfilesPage.vue'
import WorkbenchPage from '../pages/WorkbenchPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: DashboardPage, meta: { title: 'Dashboard' } },
    { path: '/workbench', component: WorkbenchPage, meta: { title: '任务工作台' } },
    { path: '/profiles', component: ProfilesPage, meta: { title: 'AI 配置' } },
    { path: '/login', component: LoginPage, meta: { title: '登录会话' } },
  ],
})

export default router
