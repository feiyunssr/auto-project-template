<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useHubSessionStore } from '../stores/useHubSessionStore'

const sessionStore = useHubSessionStore()

onMounted(() => {
  sessionStore.bootstrapSession()
})

const loginLabel = computed(() => sessionStore.state.session?.loginUrl ?? import.meta.env.VITE_HUB_LOGIN_URL ?? '/login')

function handleLogin() {
  window.location.href = loginLabel.value
}
</script>

<template>
  <main class="page-shell stack gap-6">
    <section class="panel login-panel">
      <div>
        <p class="eyebrow">Session Bridge</p>
        <h3>模板不自建账号体系，只消费 Hub 会话</h3>
        <p class="muted">
          本地开发默认允许回退到开发身份。接入真实 Hub 后，这里只负责提示当前会话状态和回跳入口。
        </p>
      </div>
      <div class="mini-stats">
        <div>
          <span class="meta-label">用户</span>
          <strong>{{ sessionStore.state.session?.hubUserName ?? sessionStore.state.session?.hubUserId ?? '未登录' }}</strong>
        </div>
        <div>
          <span class="meta-label">角色</span>
          <strong>{{ sessionStore.state.session?.role ?? '无角色' }}</strong>
        </div>
      </div>
      <div class="quick-actions">
        <button type="button" class="button button-primary" @click="handleLogin">前往 Hub 登录</button>
      </div>
    </section>
  </main>
</template>
