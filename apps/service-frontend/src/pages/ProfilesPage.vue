<script setup lang="ts">
import { onMounted } from 'vue'

import AiProfileDrawer from '../components/AiProfileDrawer.vue'
import { useAiProfileStore } from '../stores/useAiProfileStore'
import { useHubSessionStore } from '../stores/useHubSessionStore'

const sessionStore = useHubSessionStore()
const profileStore = useAiProfileStore()

onMounted(async () => {
  sessionStore.bootstrapSession()
  if (!sessionStore.isAuthenticated.value) {
    return
  }
  await profileStore.loadProfiles()
})
</script>

<template>
  <main class="page-shell stack gap-6">
    <section class="panel hero-panel">
      <div>
        <p class="eyebrow">AI Settings</p>
        <h3>模板默认暴露独立的 AI 参数中心</h3>
        <p class="muted">与 Hub 共用相同壳层和状态语义，但配置内容仍属于子服务自己的数据面。</p>
      </div>
      <button type="button" class="button button-primary" @click="profileStore.openDrawer()">新建配置</button>
    </section>

    <section class="panel">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Profiles</p>
          <h3>可用配置</h3>
        </div>
      </div>

      <div v-if="profileStore.state.loading" class="empty-state">正在加载 AI 配置...</div>
      <div v-else-if="profileStore.state.error" class="empty-state">{{ profileStore.state.error }}</div>
      <div v-else-if="!profileStore.state.items.length" class="empty-state">当前还没有 AI 配置。</div>
      <div v-else class="stack gap-4">
        <div v-for="profile in profileStore.state.items" :key="profile.id" class="advanced-box">
          <div class="row space-between align-start gap-4">
            <div class="stack gap-1">
              <strong>{{ profile.profile_name }}</strong>
              <span class="muted">{{ profile.profile_key }} · {{ profile.provider_name }} / {{ profile.model_name }}</span>
              <span class="muted">
                timeout={{ profile.timeout_ms }}ms · retries={{ profile.max_retries }} · concurrency={{ profile.concurrency_limit }}
              </span>
            </div>
            <button type="button" class="button button-secondary" @click="profileStore.openDrawer(profile)">编辑</button>
          </div>
        </div>
      </div>
    </section>

    <AiProfileDrawer />
  </main>
</template>
