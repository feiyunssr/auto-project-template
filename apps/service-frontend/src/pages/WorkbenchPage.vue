<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import AiProfileDrawer from '../components/AiProfileDrawer.vue'
import ServiceStatusBanner from '../components/ServiceStatusBanner.vue'
import TaskCreateCard from '../components/TaskCreateCard.vue'
import TaskDetailDrawer from '../components/TaskDetailDrawer.vue'
import TaskListCard from '../components/TaskListCard.vue'
import { useAiProfileStore } from '../stores/useAiProfileStore'
import { useHealthStore } from '../stores/useHealthStore'
import { useHubSessionStore } from '../stores/useHubSessionStore'
import { useTaskStore } from '../stores/useTaskStore'

const sessionStore = useHubSessionStore()
const healthStore = useHealthStore()
const taskStore = useTaskStore()
const profileStore = useAiProfileStore()

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
        <p class="eyebrow">业务工作台</p>
        <h3>任务编排与结果查看保留在模板自己的业务区</h3>
        <p class="muted">
          与 ai-auto 对齐的是壳层、数据流和运行方式，不是把 Hub 的控制面页面硬搬进来。
        </p>
      </div>
      <p class="hero-meta">统一使用 `/api/v1`、独立工作进程和右侧抽屉交互</p>
    </section>

    <ServiceStatusBanner
      :health="healthStore.state.data"
      :loading="healthStore.state.loading"
      :error="healthStore.state.error"
      :timeout-retrying="taskStore.timeoutRetryTask.value"
    />

    <section class="context-grid">
      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">提交前检查</p>
          <h3>创建任务前先做这三个检查</h3>
        </div>
        <ul class="list-dense">
          <li>业务场景和任务标题要指向同一个目标。</li>
          <li>业务输入里优先写目标、限制条件和必要背景。</li>
          <li>只有需要改模型策略时，才展开高级选项切换 AI 配置。</li>
        </ul>
        <RouterLink class="text-button" :to="{ path: '/guide', hash: '#task-flow' }">查看任务流说明</RouterLink>
      </article>

      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">状态判断</p>
          <h3>怎么判断是等待、重试还是失败</h3>
        </div>
        <ul class="list-dense">
          <li>任务处于排队中或执行中时，不要重复提交同一任务。</li>
          <li>看到警告横幅时，通常表示系统还在自动重试。</li>
          <li>只有进入失败状态，才需要重点检查尝试记录和输入质量。</li>
        </ul>
        <RouterLink class="text-button" :to="{ path: '/guide', hash: '#status-guide' }">查看状态说明</RouterLink>
      </article>
    </section>

    <section class="dashboard-grid">
      <div>
        <TaskCreateCard
          :profiles="profileStore.state.items"
          :disabled="!sessionStore.isAuthenticated.value"
          @open-profiles="profileStore.openDrawer()"
        />
      </div>
      <div>
        <TaskListCard @open-profiles="profileStore.openDrawer()" />
      </div>
    </section>

    <TaskDetailDrawer />
    <AiProfileDrawer />
  </main>
</template>
