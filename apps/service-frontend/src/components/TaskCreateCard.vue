<template>
  <section class="card stack gap-5">
    <header class="row space-between align-start">
      <div class="stack gap-1">
        <h2 class="card-title">创建任务</h2>
        <p class="card-subtitle">提交后进入异步编排流程，表单值会保留直到你主动重置。</p>
      </div>
      <button class="secondary-button" type="button" @click="$emit('open-profiles')">调整 AI 配置</button>
    </header>

    <div v-if="summaryError" class="inline-message" data-tone="danger">{{ summaryError }}</div>

    <form class="stack gap-4" @submit.prevent="submitForm">
      <label class="field-group">
        <span class="field-label">业务场景</span>
        <select ref="scenarioRef" v-model="form.scenario_key" class="field-input field-select">
          <option value="">请选择业务场景</option>
          <option value="general">通用生成</option>
          <option value="content">内容生产</option>
          <option value="video">视频脚本</option>
        </select>
        <span v-if="errors.scenario_key" class="field-error">{{ errors.scenario_key }}</span>
      </label>

      <label class="field-group">
        <span class="field-label">任务标题</span>
        <input ref="titleRef" v-model="form.title" class="field-input" placeholder="例如：春季上新广告文案" />
        <span v-if="errors.title" class="field-error">{{ errors.title }}</span>
      </label>

      <label class="field-group">
        <span class="field-label">业务输入</span>
        <textarea
          ref="briefRef"
          v-model="form.brief"
          class="field-input field-textarea"
          placeholder="请输入要交给 AI 的核心业务指令、背景和约束"
        />
        <span v-if="errors.input_payload" class="field-error">{{ errors.input_payload }}</span>
      </label>

      <label class="field-group">
        <span class="field-label">素材链接</span>
        <textarea v-model="form.asset_urls" class="field-input field-textarea" placeholder="每行一个素材 URL，可为空" />
      </label>

      <details class="advanced-box">
        <summary>高级选项</summary>
        <div class="stack gap-4 details-body">
          <label class="field-group">
            <span class="field-label">AI Profile</span>
            <select v-model="form.ai_profile_id" class="field-input field-select">
              <option value="">使用默认配置</option>
              <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
                {{ profile.profile_name }}
              </option>
            </select>
          </label>
          <label class="field-group">
            <span class="field-label">来源渠道</span>
            <input v-model="form.source_channel" class="field-input" placeholder="hub" />
          </label>
        </div>
      </details>

      <div class="row gap-3">
        <button class="primary-button" type="submit" :disabled="taskState.submitting || disabled">
          {{ taskState.submitting ? "已提交，处理中..." : "提交任务" }}
        </button>
        <button class="secondary-button" type="button" :disabled="taskState.submitting" @click="resetForm">新建任务</button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import type { AiProfile } from '../api/types'
import { useTaskStore } from '../stores/useTaskStore'

const props = defineProps<{ profiles: readonly AiProfile[]; disabled: boolean }>();
defineEmits<{ (event: "open-profiles"): void }>();

const taskStore = useTaskStore();
const { state: taskState } = taskStore;

const scenarioRef = ref<HTMLSelectElement | null>(null);
const titleRef = ref<HTMLInputElement | null>(null);
const briefRef = ref<HTMLTextAreaElement | null>(null);

const form = reactive({
  scenario_key: "general",
  title: "",
  brief: "",
  asset_urls: "",
  ai_profile_id: "",
  source_channel: "hub",
});

const errors = reactive<Record<string, string>>({});
const validationSummary = ref("");

const summaryError = computed(() => validationSummary.value || taskState.createError || "");

function resetForm() {
  form.title = "";
  form.brief = "";
  form.asset_urls = "";
  validationSummary.value = "";
  Object.keys(errors).forEach((key) => delete errors[key]);
}

function validate() {
  Object.keys(errors).forEach((key) => delete errors[key]);
  if (!form.scenario_key) errors.scenario_key = "请选择业务场景";
  if (!form.title.trim()) errors.title = "请输入任务标题";
  if (!form.brief.trim()) errors.input_payload = "请输入业务输入";
  validationSummary.value = Object.keys(errors).length ? "提交失败，请先修正表单中的必填项。" : "";
  return Object.keys(errors).length === 0;
}

function focusFirstError() {
  if (errors.scenario_key) scenarioRef.value?.focus();
  else if (errors.title) titleRef.value?.focus();
  else if (errors.input_payload) briefRef.value?.focus();
}

async function submitForm() {
  if (!validate()) {
    focusFirstError();
    return;
  }
  validationSummary.value = "";
  try {
    await taskStore.createNewTask({
      scenario_key: form.scenario_key,
      title: form.title.trim(),
      ai_profile_id: form.ai_profile_id || null,
      source_channel: form.source_channel || "hub",
      input_payload: {
        brief: form.brief.trim(),
        asset_urls: form.asset_urls
          .split("\n")
          .map((item) => item.trim())
          .filter(Boolean),
      },
    });
  } catch {
    Object.assign(errors, taskState.fieldErrors);
    validationSummary.value = "提交失败，请检查高亮字段后重试。";
    focusFirstError();
  }
}
</script>
