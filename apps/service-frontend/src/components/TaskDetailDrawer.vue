<template>
  <teleport to="body">
    <div v-if="taskState.selectedTaskId" class="drawer-shell">
      <button class="drawer-backdrop" type="button" @click="taskStore.closeDetail()" />
      <aside class="drawer-panel stack gap-6">
        <header class="row space-between align-start">
          <div class="stack gap-1">
            <h2 class="card-title">任务详情</h2>
            <p class="card-subtitle">{{ detail?.job_no ?? "正在加载任务详情" }}</p>
          </div>
          <button class="secondary-button" type="button" @click="taskStore.closeDetail()">关闭</button>
        </header>

        <div v-if="taskState.detailError" class="inline-message" data-tone="danger">
          {{ taskState.detailError }}
        </div>
        <div v-if="taskState.loadingDetail && !detail" class="empty-state">任务详情加载中...</div>
        <template v-else-if="detail">
          <section class="drawer-section">
            <div class="row space-between align-start">
              <div>
                <TaskStatusBadge :status="detail.status" />
                <p class="muted-text">{{ detail.title }}</p>
              </div>
              <button
                v-if="detail.retryable"
                class="primary-button"
                type="button"
                :disabled="taskState.retryingIds.includes(detail.id)"
                @click="taskStore.retryExistingTask(detail.id)"
              >
                {{ taskState.retryingIds.includes(detail.id) ? "重试中..." : "重试本次任务" }}
              </button>
            </div>
            <div class="meta-grid">
              <div><span class="meta-label">提交人</span><strong>{{ detail.submitted_by_name || detail.submitted_by_hub_user_id }}</strong></div>
              <div><span class="meta-label">场景</span><strong>{{ detail.scenario_key }}</strong></div>
              <div><span class="meta-label">更新时间</span><strong>{{ formatDateTime(detail.updated_at) }}</strong></div>
              <div><span class="meta-label">最大重试</span><strong>{{ detail.max_retries ?? "--" }}</strong></div>
            </div>
          </section>

          <section v-if="detail.status === 'review_required'" class="inline-message" data-tone="warning">
            任务已完成，但结果仍需人工复核。
          </section>
          <section
            v-if="detail.status === 'running' && detail.error_code === 'PROVIDER_TIMEOUT_RETRYING'"
            class="inline-message"
            data-tone="warning"
          >
            第 {{ detail.current_attempt_no }} 次尝试已超时，系统将继续重试；详情面板会保留最近一次成功结果。
          </section>
          <section v-if="detail.error_message" class="inline-message" data-tone="danger">
            {{ detail.error_message }}
          </section>
          <section v-if="detail.last_success_result && detail.status === 'failed'" class="inline-message" data-tone="warning">
            当前重跑失败，以下展示最近一次成功结果。
          </section>

          <section class="drawer-section stack gap-4">
            <h3 class="section-title">执行时间线</h3>
            <div v-if="!detail.attempts.length" class="empty-state subtle">任务已提交，正在调用 AI 处理</div>
            <ol v-else class="timeline">
              <li v-for="attempt in detail.attempts" :key="attempt.id">
                <div class="row space-between">
                  <strong>第 {{ attempt.attempt_no }} 次 / {{ attempt.provider_model }}</strong>
                  <span class="muted-text">{{ formatDateTime(attempt.started_at) }}</span>
                </div>
                <p class="muted-text">
                  {{ attempt.status }} · {{ attempt.error_message || attempt.error_code || "调用中" }}
                </p>
              </li>
            </ol>
          </section>

          <section class="drawer-section stack gap-4">
            <h3 class="section-title">结果预览</h3>
            <pre v-if="activeResult" class="code-block">{{ formatJson(activeResult.structured_payload) }}</pre>
            <div v-else class="empty-state subtle">结果骨架占位中，等待执行完成。</div>
          </section>

          <section class="drawer-section stack gap-4">
            <h3 class="section-title">素材与输入</h3>
            <pre class="code-block">{{ formatJson(detail.input_payload) }}</pre>
            <ul v-if="detail.artifacts.length" class="artifact-list">
              <li v-for="artifact in detail.artifacts" :key="artifact.id">
                <span>{{ artifact.artifact_role }}</span>
                <a :href="artifact.uri" target="_blank" rel="noreferrer">{{ artifact.uri }}</a>
              </li>
            </ul>
          </section>
        </template>
      </aside>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { formatDateTime, formatJson } from '../utils/format'
import { useTaskStore } from '../stores/useTaskStore'
import TaskStatusBadge from "./TaskStatusBadge.vue";

const taskStore = useTaskStore();
const { state: taskState, selectedTask: detail } = taskStore;

const activeResult = computed(() => detail.value?.results[0] ?? detail.value?.last_success_result ?? null);
</script>
