<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import ServiceStatusBanner from '../components/ServiceStatusBanner.vue'
import { useAiProfileStore } from '../stores/useAiProfileStore'
import { useHealthStore } from '../stores/useHealthStore'
import { useHubSessionStore } from '../stores/useHubSessionStore'
import { useTaskStore } from '../stores/useTaskStore'
import { healthStatusLabel } from '../utils/format'

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
        <p class="eyebrow">模板基线</p>
        <h3>数据面模板继承与 ai-auto 一致的控制台骨架</h3>
        <p class="muted">
          子服务模板现在与 Hub 一样使用路由化壳层、统一 API 前缀、独立工作进程和共享部署基线。
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
          <p class="eyebrow">运行概览</p>
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
          <strong>{{ healthStatusLabel(healthStore.state.data?.status) }}</strong>
        </div>
      </div>

      <div class="quick-actions">
        <RouterLink class="button button-primary" to="/workbench">进入任务工作台</RouterLink>
        <RouterLink class="button button-secondary" to="/profiles">查看 AI 配置</RouterLink>
        <RouterLink class="button button-secondary" :to="{ path: '/guide', hash: '#quick-start' }">快速上手</RouterLink>
        <RouterLink class="button button-secondary" to="/login">检查登录桥接</RouterLink>
      </div>
    </section>

    <section class="context-grid">
      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">初次使用</p>
          <h3>第一次使用建议先看这 3 件事</h3>
        </div>
        <ul class="list-dense">
          <li>先确认登录态是否正常，再提交任务。</li>
          <li>任务标题写清业务目标，业务输入写清约束与背景。</li>
          <li>遇到待复核状态时，把它当作待人工判断，不要直接视为失败。</li>
        </ul>
        <RouterLink class="text-button" :to="{ path: '/guide', hash: '#quick-start' }">查看完整教程</RouterLink>
      </article>

      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">异常处理</p>
          <h3>遇到异常时先看状态，再看尝试记录</h3>
        </div>
        <ul class="list-dense">
          <li>警告横幅通常代表系统正在自动重试，不是最终失败。</li>
          <li>进入失败状态后，优先看任务详情里的最近一次尝试和错误说明。</li>
          <li>如果频繁超时，再回到 AI 配置页调整超时和重试策略。</li>
        </ul>
        <RouterLink class="text-button" :to="{ path: '/guide', hash: '#troubleshooting' }">查看排错指南</RouterLink>
      </article>
    </section>
  </main>
</template>
