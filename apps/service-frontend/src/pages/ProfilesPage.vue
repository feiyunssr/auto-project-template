<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'

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

    <section id="profile-help" class="context-grid">
      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">When To Edit</p>
          <h3>AI 配置不是每次任务都要改</h3>
        </div>
        <ul class="list-dense">
          <li>默认配置覆盖大多数业务场景，先让流程跑通。</li>
          <li>频繁超时、风格不稳定或并发不合适时，再调整 Profile。</li>
          <li>修改只影响后续新任务，不会回写历史结果。</li>
        </ul>
        <RouterLink class="text-button" :to="{ path: '/guide', hash: '#profiles-guide' }">查看配置策略</RouterLink>
      </article>

      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">Checklist</p>
          <h3>新建配置时优先核对这些字段</h3>
        </div>
        <ul class="list-dense">
          <li>`timeout_ms` 决定单次调用容忍时长。</li>
          <li>`max_retries` 决定超时或暂时性失败时还能重试几次。</li>
          <li>`concurrency_limit` 过高会增加外部 Provider 压力。</li>
        </ul>
        <button type="button" class="text-button" @click="profileStore.openDrawer()">立即新建配置</button>
      </article>
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
