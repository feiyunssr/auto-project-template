<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import ServiceStatusBanner from '../components/ServiceStatusBanner.vue'
import { useAiProfileStore } from '../stores/useAiProfileStore'
import { useHealthStore } from '../stores/useHealthStore'
import { useHubSessionStore } from '../stores/useHubSessionStore'
import { useTaskStore } from '../stores/useTaskStore'

const sessionStore = useHubSessionStore()
const healthStore = useHealthStore()
const taskStore = useTaskStore()
const profileStore = useAiProfileStore()

const runningCount = computed(() =>
  taskStore.state.items.filter((item) => item.status === 'queued' || item.status === 'running').length,
)
const reviewCount = computed(() => taskStore.state.items.filter((item) => item.status === 'review_required').length)
const profileCount = computed(() => profileStore.state.items.length)

onMounted(async () => {
  sessionStore.bootstrapSession()
  await healthStore.loadHealth()
  if (!sessionStore.isAuthenticated.value) {
    taskStore.stopPolling()
    return
  }
  await Promise.all([taskStore.loadList(), profileStore.loadProfiles()])
  taskStore.startPolling()
})

onBeforeUnmount(() => {
  taskStore.stopPolling()
})
</script>

<template>
  <main class="page-shell stack gap-6">
    <section class="panel hero-panel">
      <div>
        <p class="eyebrow">Template Baseline</p>
        <h3>数据面模板继承与 ai-auto 一致的控制台骨架</h3>
        <p class="muted">
          子服务模板现在与 Hub 一样使用路由化壳层、统一 API 前缀、独立 worker 和共享部署基线。
        </p>
      </div>
      <p class="hero-meta">
        {{ sessionStore.isAuthenticated.value ? '当前已连接 Hub 会话' : '当前使用本地开发会话' }}
      </p>
    </section>

    <ServiceStatusBanner
      :health="healthStore.state.data"
      :loading="healthStore.state.loading"
      :error="healthStore.state.error"
      :timeout-retrying="taskStore.timeoutRetryTask.value"
    />

    <section class="panel">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Operational Snapshot</p>
          <h3>模板运行概览</h3>
          <p class="muted">这里展示模板与 Hub 对齐后的默认运行面板，不掺入控制面专属治理逻辑。</p>
        </div>
      </div>

      <div class="mini-stats">
        <div>
          <span class="meta-label">运行中/排队中任务</span>
          <strong>{{ runningCount }}</strong>
        </div>
        <div>
          <span class="meta-label">待复核任务</span>
          <strong>{{ reviewCount }}</strong>
        </div>
        <div>
          <span class="meta-label">AI 配置数量</span>
          <strong>{{ profileCount }}</strong>
        </div>
        <div>
          <span class="meta-label">健康状态</span>
          <strong>{{ healthStore.state.data?.status ?? '--' }}</strong>
        </div>
      </div>

      <div class="quick-actions">
        <RouterLink class="button button-primary" to="/workbench">进入任务工作台</RouterLink>
        <RouterLink class="button button-secondary" to="/profiles">查看 AI 配置</RouterLink>
        <RouterLink class="button button-secondary" to="/login">检查登录桥接</RouterLink>
      </div>
    </section>
  </main>
</template>
