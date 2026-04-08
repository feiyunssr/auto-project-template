<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import { useHubSessionStore } from '../stores/useHubSessionStore'
import { roleLabel } from '../utils/format'

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
        <p class="eyebrow">会话桥接</p>
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
          <strong>{{ roleLabel(sessionStore.state.session?.role) }}</strong>
        </div>
      </div>
      <div class="quick-actions">
        <button type="button" class="button button-primary" @click="handleLogin">前往 Hub 登录</button>
        <RouterLink class="button button-secondary" :to="{ path: '/guide', hash: '#session-guide' }">查看会话说明</RouterLink>
      </div>
    </section>

    <section class="context-grid">
      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">会话为何重要</p>
          <h3>会话异常会直接阻断业务区操作</h3>
        </div>
        <ul class="list-dense">
          <li>模板依赖 Hub 登录态，不在本地维护独立账号系统。</li>
          <li>会话失效后会暂停提交和轮询，防止把鉴权问题误记成任务失败。</li>
          <li>本地开发是否允许回退身份，取决于环境开关。</li>
        </ul>
      </article>

      <article class="panel context-card stack gap-4">
        <div>
          <p class="eyebrow">登录失败排查</p>
          <h3>登录后仍不可用时先检查这几项</h3>
        </div>
        <ul class="list-dense">
          <li>确认 Hub 回跳地址和当前服务地址一致。</li>
          <li>确认浏览器没有阻止会话 Cookie 或身份头注入。</li>
          <li>重新进入工作台，看顶部横幅是否还在提示会话失效。</li>
        </ul>
        <RouterLink class="text-button" :to="{ path: '/guide', hash: '#faq' }">查看常见问题</RouterLink>
      </article>
    </section>
  </main>
</template>
