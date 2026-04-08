import { createRouter, createWebHistory } from 'vue-router'

import DashboardPage from '../pages/DashboardPage.vue'
import GuidePage from '../pages/GuidePage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ProfilesPage from '../pages/ProfilesPage.vue'
import WorkbenchPage from '../pages/WorkbenchPage.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }

    if (to.hash) {
      return {
        el: to.hash,
        top: 96,
        behavior: 'smooth',
      }
    }

    if (to.path !== from.path) {
      return { top: 0 }
    }

    return undefined
  },
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: DashboardPage, meta: { title: '总览面板' } },
    { path: '/guide', component: GuidePage, meta: { title: '使用教程' } },
    { path: '/workbench', component: WorkbenchPage, meta: { title: '任务工作台' } },
    { path: '/profiles', component: ProfilesPage, meta: { title: 'AI 配置' } },
    { path: '/login', component: LoginPage, meta: { title: '登录会话' } },
  ],
})

export default router
