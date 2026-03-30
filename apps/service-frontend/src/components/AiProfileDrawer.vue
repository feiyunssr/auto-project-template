<template>
  <teleport to="body">
    <div v-if="profileState.drawerOpen" class="drawer-shell">
      <button class="drawer-backdrop" type="button" @click="profileStore.closeDrawer()" />
      <aside class="drawer-panel stack gap-5">
        <header class="row space-between align-start">
          <div class="stack gap-1">
            <h2 class="card-title">AI 配置</h2>
            <p class="card-subtitle">保存失败时不会清空当前编辑内容。</p>
          </div>
          <button class="secondary-button" type="button" @click="profileStore.closeDrawer()">关闭</button>
        </header>

        <div v-if="profileState.error" class="inline-message" data-tone="danger">{{ profileState.error }}</div>

        <label class="field-group">
          <span class="field-label">选择已有配置</span>
          <select class="field-input field-select" @change="selectExisting">
            <option value="">新建或当前草稿</option>
            <option v-for="profile in profileState.items" :key="profile.id" :value="profile.id">
              {{ profile.profile_name }}
            </option>
          </select>
        </label>

        <div class="stack gap-4">
          <label class="field-group"><span class="field-label">Profile Key</span><input class="field-input" :value="profileState.draft.profile_key" @input="patch('profile_key', $event)" /></label>
          <label class="field-group"><span class="field-label">配置名称</span><input class="field-input" :value="profileState.draft.profile_name" @input="patch('profile_name', $event)" /></label>
          <label class="field-group"><span class="field-label">模型</span><input class="field-input" :value="profileState.draft.model_name" @input="patch('model_name', $event)" /></label>
          <label class="field-group"><span class="field-label">系统提示词</span><textarea class="field-input field-textarea" :value="profileState.draft.system_prompt" @input="patch('system_prompt', $event)" /></label>
          <label class="field-group"><span class="field-label">Prompt 模板</span><textarea class="field-input field-textarea" :value="profileState.draft.prompt_template" @input="patch('prompt_template', $event)" /></label>
          <div class="meta-grid">
            <label class="field-group"><span class="field-label">超时 ms</span><input class="field-input" type="number" :value="profileState.draft.timeout_ms" @input="patchNumber('timeout_ms', $event)" /></label>
            <label class="field-group"><span class="field-label">最大重试</span><input class="field-input" type="number" :value="profileState.draft.max_retries" @input="patchNumber('max_retries', $event)" /></label>
            <label class="field-group"><span class="field-label">并发限制</span><input class="field-input" type="number" :value="profileState.draft.concurrency_limit" @input="patchNumber('concurrency_limit', $event)" /></label>
            <label class="field-group"><span class="field-label">Max Tokens</span><input class="field-input" type="number" :value="profileState.draft.max_tokens" @input="patchNumber('max_tokens', $event)" /></label>
          </div>
        </div>

        <div class="row gap-3">
          <button class="primary-button" type="button" :disabled="profileState.saving" @click="profileStore.saveDraft()">
            {{ profileState.saving ? "保存中..." : "保存配置" }}
          </button>
          <p class="muted-text">timeout / retries 仅影响后续新任务。</p>
        </div>
      </aside>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import type { AiProfile } from '../api/types'
import type { AiProfileDraft } from '../stores/useAiProfileStore'
import { useAiProfileStore } from '../stores/useAiProfileStore'

const profileStore = useAiProfileStore();
const { state: profileState } = profileStore;

function selectExisting(event: Event) {
  const id = (event.target as HTMLSelectElement).value;
  const profile = profileState.items.find((item) => item.id === id);
  profileStore.hydrateDraft(profile as AiProfile | undefined);
}

function patch(field: keyof AiProfileDraft, event: Event) {
  profileStore.patchDraft({ [field]: (event.target as HTMLInputElement | HTMLTextAreaElement).value });
}

function patchNumber(field: keyof AiProfileDraft, event: Event) {
  profileStore.patchDraft({ [field]: Number((event.target as HTMLInputElement).value) });
}
</script>
