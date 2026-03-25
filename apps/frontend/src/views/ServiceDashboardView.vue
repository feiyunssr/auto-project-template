<template>
  <main class="page-shell stack gap-6">
    <ServiceStatusBanner
      :health="healthState.data"
      :loading="healthState.loading"
      :error="healthState.error"
      :timeout-retrying="taskStore.timeoutRetryTask.value"
    />

    <section class="dashboard-grid">
      <TaskCreateCard
        :profiles="profileState.items"
        :disabled="!sessionStore.isAuthenticated.value"
        @open-profiles="profileStore.openDrawer()"
      />
      <TaskListCard @open-profiles="profileStore.openDrawer()" />
    </section>

    <TaskDetailDrawer />
    <AiProfileDrawer />
  </main>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";

import AiProfileDrawer from "../components/AiProfileDrawer.vue";
import ServiceStatusBanner from "../components/ServiceStatusBanner.vue";
import TaskCreateCard from "../components/TaskCreateCard.vue";
import TaskDetailDrawer from "../components/TaskDetailDrawer.vue";
import TaskListCard from "../components/TaskListCard.vue";
import { useAiProfileStore } from "../stores/useAiProfileStore";
import { useHealthStore } from "../stores/useHealthStore";
import { useHubSessionStore } from "../stores/useHubSessionStore";
import { useTaskStore } from "../stores/useTaskStore";

const sessionStore = useHubSessionStore();
const healthStore = useHealthStore();
const taskStore = useTaskStore();
const profileStore = useAiProfileStore();

const { state: healthState } = healthStore;
const { state: profileState } = profileStore;

onMounted(async () => {
  sessionStore.bootstrapSession();
  if (!sessionStore.isAuthenticated.value) {
    taskStore.stopPolling();
    return;
  }
  await Promise.all([healthStore.loadHealth(), taskStore.loadList(), profileStore.loadProfiles()]);
  taskStore.startPolling();
});

onBeforeUnmount(() => {
  taskStore.stopPolling();
});
</script>
