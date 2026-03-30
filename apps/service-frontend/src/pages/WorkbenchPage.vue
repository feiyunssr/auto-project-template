<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

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
        <p class="eyebrow">Service Workbench</p>
        <h3>任务编排与结果查看保留在模板自己的业务区</h3>
        <p class="muted">
          与 ai-auto 对齐的是壳层、数据流和运行方式，不是把 Hub 的控制面页面硬搬进来。
        </p>
      </div>
      <p class="hero-meta">统一使用 `/api/v1`、独立 worker 和右侧抽屉交互</p>
    </section>

    <ServiceStatusBanner
      :health="healthStore.state.data"
      :loading="healthStore.state.loading"
      :error="healthStore.state.error"
      :timeout-retrying="taskStore.timeoutRetryTask.value"
    />

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
