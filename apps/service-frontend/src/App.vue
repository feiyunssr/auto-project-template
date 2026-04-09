<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import { restoreSession } from './composables/session'
import { useHubSessionStore } from './stores/useHubSessionStore'
import { roleLabel } from './utils/format'

const route = useRoute()
const sessionStore = useHubSessionStore()
const { state: sessionState, isAuthenticated } = sessionStore

onMounted(() => {
  void restoreSession()
})

const navItems = computed(() => [
  { to: '/dashboard', label: '概览' },
  { to: '/guide', label: '使用教程' },
  { to: '/workbench', label: '任务工作台' },
  { to: '/profiles', label: 'AI 配置' },
  { to: '/login', label: isAuthenticated.value ? '会话' : '登录' },
])

const shellEyebrow = computed(() => {
  if (sessionState.authExpired) {
    return '会话受阻'
  }

  return isAuthenticated.value ? '已连接 Hub' : '本地开发会话'
})

const currentUserLabel = computed(() => sessionState.session?.hubUserName ?? sessionState.session?.hubUserId ?? '未登录')
const currentRoleLabel = computed(() => roleLabel(sessionState.session?.role))

const sessionDescription = computed(() => {
  if (sessionState.authExpired) {
    return '当前会话已失效，业务区会暂停提交和轮询，并自动回到 Hub 登录页。'
  }

  return '模板默认继承 ai-auto 的路由壳层、配色语义、工作进程拆分与部署基线，业务区只补自身流程。'
})

const statusLabel = computed(() => {
  if (sessionState.authExpired) {
    return '会话失效'
  }

  return isAuthenticated.value ? '已连接 Hub' : '等待会话'
})

const hubHomeUrl = computed(() => {
  const rawUrl = sessionStore.loginUrl.value

  if (!rawUrl) {
    return '/dashboard'
  }

  try {
    const resolved = new URL(rawUrl, window.location.origin)
    resolved.search = ''
    resolved.hash = ''
    resolved.pathname = resolved.pathname.replace(/\/login\/?$/, '/dashboard')
    return resolved.toString()
  } catch {
    return rawUrl.replace(/\/login(?:\/)?(?:\?.*)?$/, '/dashboard')
  }
})

function isActive(path: string) {
  return route.path === path || route.path.startsWith(`${path}/`)
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">{{ shellEyebrow }}</p>
        <h1>子服务工作台</h1>
        <p class="muted">{{ sessionDescription }}</p>
      </div>

      <nav class="nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: isActive(item.to) }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="sidebar-session panel">
        <p class="eyebrow">当前会话</p>
        <strong>{{ currentUserLabel }}</strong>
        <p class="muted">{{ currentRoleLabel }}</p>
        <p class="muted sidebar-status">{{ statusLabel }}</p>
        <RouterLink class="button button-primary sidebar-action" to="/login">
          {{ isAuthenticated ? '查看会话' : '去登录' }}
        </RouterLink>
        <a class="button button-secondary sidebar-action" :href="hubHomeUrl">返回 Hub</a>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <p class="eyebrow">工作区</p>
          <h2>{{ route.meta.title ?? 'AI Auto 子服务模板' }}</h2>
        </div>
        <p class="muted topbar-meta">
          以 `ai-auto` 为基准统一工程和视觉基线，但保留数据面模板自己的任务编排职责。
        </p>
      </header>

      <RouterView />
    </main>
  </div>
</template>
