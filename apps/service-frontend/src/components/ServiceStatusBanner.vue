<template>
  <section class="stack gap-3">
    <div v-if="sessionState.authExpired" class="banner" data-tone="danger">
      <div>
        <strong>当前会话已失效</strong>
        <p>{{ sessionState.overlayMessage }}</p>
      </div>
      <button class="secondary-button" type="button" @click="redirectToLogin">返回登录</button>
    </div>
    <div v-else-if="timeoutRetrying" class="banner" data-tone="warning">
      <div>
        <strong>AI 响应较慢，系统正在重试</strong>
        <p>
          {{ timeoutRetrying.title }}（{{ timeoutRetrying.jobNo }}）在第 {{ timeoutRetrying.currentAttemptNo }} 次尝试超时，
          系统将继续重试，最多允许 {{ timeoutRetrying.maxRetries }} 次重试。
        </p>
      </div>
    </div>
    <div class="banner" :data-tone="healthTone">
      <div>
        <strong>{{ title }}</strong>
        <p>{{ description }}</p>
      </div>
      <div class="banner-metrics">
        <span>排队 {{ health?.metrics.queued_jobs ?? 0 }}</span>
        <span>运行 {{ health?.metrics.running_jobs ?? 0 }}</span>
        <span>实例 {{ health?.instance_id?.slice(0, 8) ?? "--" }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { HealthResponse } from '../api/types'
import { formatRelativeSeconds, registrationStatusLabel, translateErrorMessage } from '../utils/format'
import { useHubSessionStore } from '../stores/useHubSessionStore'

const props = defineProps<{
  health: HealthResponse | null;
  loading: boolean;
  error: string;
  timeoutRetrying:
    | {
        jobNo: string;
        title: string;
        currentAttemptNo: number;
        maxRetries: number;
      }
    | null;
}>();

const { state: sessionState } = useHubSessionStore();

const healthTone = computed(() => {
  if (props.error) return "danger";
  if (props.health?.status === "degraded") return "warning";
  if (props.health?.status === "healthy") return "success";
  return "neutral";
});

const title = computed(() => {
  if (props.loading) return "正在加载服务健康摘要";
  if (props.error) return "服务摘要获取失败";
  if (props.health?.status === "degraded") return "服务处于降级状态";
  return "服务运行正常";
});

const description = computed(() => {
  if (props.error) return translateErrorMessage(props.error);
  if (!props.health) return "等待健康检查结果。";
  const registration = registrationStatusLabel(String(props.health.registration?.status ?? "unknown"));
  return `注册状态：${registration}，运行时长：${formatRelativeSeconds(props.health.uptime_sec)}。`;
});

function redirectToLogin() {
  const loginUrl = sessionState.session?.loginUrl ?? import.meta.env.VITE_HUB_LOGIN_URL ?? "/login";
  window.location.href = loginUrl;
}
</script>
