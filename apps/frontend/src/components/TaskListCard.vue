<template>
  <section class="card stack gap-5">
    <header class="row space-between align-start">
      <div class="stack gap-1">
        <h2 class="card-title">任务列表</h2>
        <p class="card-subtitle">保留最近一次成功数据，轮询失败时不清空列表。</p>
      </div>
      <div class="row gap-3">
        <select class="field-input field-select" :value="taskState.filterStatus" @change="onFilterChange">
          <option value="">全部状态</option>
          <option value="queued">排队中</option>
          <option value="running">执行中</option>
          <option value="succeeded">已完成</option>
          <option value="failed">失败</option>
          <option value="review_required">待复核</option>
        </select>
        <button class="secondary-button" type="button" @click="$emit('open-profiles')">AI 配置</button>
      </div>
    </header>

    <div v-if="taskState.listError" class="inline-message" data-tone="danger">{{ taskState.listError }}</div>
    <div v-if="taskState.loadingList && !taskState.items.length" class="empty-state">任务列表加载中...</div>
    <div v-else-if="!taskState.items.length" class="empty-state">暂无任务，可先提交一个业务请求。</div>

    <table v-else class="task-table">
      <thead>
        <tr>
          <th>任务</th>
          <th>状态</th>
          <th>尝试</th>
          <th>更新时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in taskState.items" :key="task.id">
          <td>
            <button class="table-link" type="button" @click="openDetail(task.id)">
              {{ task.title }}
            </button>
            <p class="muted-text">{{ task.job_no }} / {{ task.scenario_key }}</p>
          </td>
          <td>
            <TaskStatusBadge :status="task.status" />
            <p class="muted-text">{{ secondaryText(task) }}</p>
          </td>
          <td>{{ task.current_attempt_no || 0 }}</td>
          <td>{{ formatDateTime(task.updated_at) }}</td>
          <td>
            <button class="text-button" type="button" @click="openDetail(task.id)">查看详情</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import type { TaskSummary } from "../lib/types";
import { formatDateTime } from "../lib/format";
import { useTaskStore } from "../stores/useTaskStore";
import TaskStatusBadge from "./TaskStatusBadge.vue";

defineEmits<{ (event: "open-profiles"): void }>();

const taskStore = useTaskStore();
const { state: taskState } = taskStore;

function onFilterChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  taskStore.loadList(target.value);
}

function openDetail(taskId: string) {
  taskStore.loadDetail(taskId);
}

function secondaryText(task: TaskSummary) {
  if (task.error_code === "PROVIDER_TIMEOUT_RETRYING") {
    return "响应较慢，正在重试";
  }
  if (task.status === "review_required") {
    return "结果已生成，等待人工复核";
  }
  return String(task.result_summary?.message ?? task.error_message ?? "最近已同步");
}
</script>
