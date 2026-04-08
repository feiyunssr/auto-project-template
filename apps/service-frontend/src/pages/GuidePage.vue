<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { statusLabel } from '../utils/format'

const statusItems = [
  {
    key: 'queued',
    label: '排队中',
    tone: 'neutral',
    description: '任务已入队，等待工作进程领取。此时不需要重复提交。',
  },
  {
    key: 'running',
    label: '执行中',
    tone: 'neutral',
    description: '系统正在调用模型服务或整理结果，详情抽屉会持续刷新尝试记录。',
  },
  {
    key: 'succeeded',
    label: '已完成',
    tone: 'success',
    description: '任务已成功落结果，可进入详情继续查看输出摘要和产物链接。',
  },
  {
    key: 'review_required',
    label: '待复核',
    tone: 'warning',
    description: '结果已经生成，但仍需要人工判断是否可用，不应按失败处理。',
  },
  {
    key: 'failed',
    label: '失败',
    tone: 'danger',
    description: '任务已达到最终失败态，优先检查输入、AI 配置、超时和最近一次尝试记录。',
  },
]

const faqItems = [
  {
    question: '为什么我点击提交后没有立刻看到结果？',
    answer:
      '本服务采用异步编排。提交后任务会先进入队列，再由工作进程执行，所以正确预期是先看状态，再看结果，而不是等待同步返回。',
  },
  {
    question: 'AI 响应较慢，系统正在重试是什么意思？',
    answer:
      '这表示当前尝试记录超时，但系统还没有判定最终失败。只要仍显示警告提示，就说明后台还在自动重试。',
  },
  {
    question: '什么时候应该调整 AI 配置？',
    answer:
      '当你需要改变超时、重试次数、模型或并发限制时再调整。日常提交任务不必每次都改，默认配置应覆盖大多数场景。',
  },
  {
    question: '会话失效后为什么不能继续操作？',
    answer:
      '模板依赖 Hub 会话。会话失效时会暂停提交与轮询，避免把未授权状态误记录成业务失败。',
  },
  {
    question: '失败后第一步该看哪里？',
    answer:
      '先看任务详情中的最近一次尝试记录和错误信息，再确认业务输入是否完整、AI 配置是否过于激进、素材链接是否可访问。',
  },
]
</script>

<template>
  <main class="page-shell stack gap-6">
    <section class="panel hero-panel">
      <div>
        <p class="eyebrow">帮助中心</p>
        <h3>把首次上手、状态判断和故障排查放到同一个帮助中心</h3>
        <p class="muted">
          教程页负责系统说明，页面内帮助负责就地解释。两者配合，用户不需要在长文档和业务区之间来回切换。
        </p>
      </div>
      <div class="stack gap-3 align-end">
        <RouterLink class="button button-primary" to="/workbench">去创建任务</RouterLink>
        <RouterLink class="button button-secondary" to="/profiles">查看 AI 配置</RouterLink>
      </div>
    </section>

    <section class="guide-layout">
      <aside class="panel guide-nav">
        <p class="eyebrow">跳转目录</p>
        <a class="guide-nav-link" href="#quick-start">3 步快速开始</a>
        <a class="guide-nav-link" href="#task-flow">任务流说明</a>
        <a class="guide-nav-link" href="#status-guide">状态判断</a>
        <a class="guide-nav-link" href="#profiles-guide">AI 配置策略</a>
        <a class="guide-nav-link" href="#session-guide">登录与会话</a>
        <a class="guide-nav-link" href="#troubleshooting">故障排查</a>
        <a class="guide-nav-link" href="#faq">常见问题</a>
      </aside>

      <div class="guide-content stack gap-6">
        <section id="quick-start" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">快速开始</p>
              <h3>3 步完成第一次任务</h3>
            </div>
          </div>

          <ol class="numbered-list">
            <li>
              先在 <RouterLink to="/login">登录会话</RouterLink> 确认当前身份有效。如果你在本地开发环境，页面会说明是否启用了开发回退身份。
            </li>
            <li>
              打开 <RouterLink to="/workbench">任务工作台</RouterLink>，填写业务场景、任务标题和业务输入。只有当你需要改变模型策略时，才去高级选项切换 AI 配置。
            </li>
            <li>
              提交后盯住状态横幅和任务列表，必要时打开详情抽屉查看尝试记录。不要在排队中或执行中重复提交同一任务。
            </li>
          </ol>
        </section>

        <section id="task-flow" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">任务流程</p>
              <h3>任务是怎样从输入走到结果的</h3>
            </div>
          </div>

          <div class="context-grid">
            <article class="advanced-box context-card stack gap-3">
              <strong>提交输入</strong>
              <p class="muted">
                标题用于识别任务，业务输入用于告诉 AI 目标与限制，素材链接用于补上下文。三者要围绕同一个业务动作，不要混入无关信息。
              </p>
            </article>
            <article class="advanced-box context-card stack gap-3">
              <strong>异步编排</strong>
              <p class="muted">
                后端会把任务放进队列，由工作进程领取并调用模型服务。耗时长是正常现象，所以列表和详情是主视图，不是弹窗结果。
              </p>
            </article>
            <article class="advanced-box context-card stack gap-3">
              <strong>结果落库</strong>
              <p class="muted">
                成功后结果会保存为可回查记录。即使失败，也应该保留任务号、尝试记录和错误信息，方便定位问题和重新提交。
              </p>
            </article>
          </div>

          <div class="inline-message">
            <strong>实操建议</strong>
            <p>如果你的目标不明确，先缩小输入范围；如果你的输入很长，优先保留任务目标、限制条件和关键素材。</p>
          </div>
        </section>

        <section id="status-guide" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">状态说明</p>
              <h3>如何读懂任务状态</h3>
            </div>
          </div>

          <div class="status-grid">
            <article v-for="item in statusItems" :key="item.key" class="advanced-box context-card stack gap-3">
              <div class="row space-between">
                <strong>{{ item.label }}</strong>
                <span class="status-badge" :data-tone="item.tone">{{ statusLabel(item.key) }}</span>
              </div>
              <p class="muted">{{ item.description }}</p>
            </article>
          </div>
        </section>

        <section id="profiles-guide" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">AI 配置</p>
              <h3>什么时候该调 AI 配置，什么时候不该</h3>
            </div>
          </div>

          <ul class="list-dense">
            <li>默认配置适合大多数任务，不要把 AI 配置当成每次必改的输入项。</li>
            <li>当你连续遇到超时、结果风格不稳定或并发限制不合理时，再去改超时、重试次数、模型和并发限制。</li>
            <li>AI 配置影响的是后续新任务，不会回溯修改历史记录。</li>
          </ul>

          <div class="quick-actions">
            <RouterLink class="button button-secondary" :to="{ path: '/profiles', hash: '#profile-help' }">
              去看配置说明
            </RouterLink>
          </div>
        </section>

        <section id="session-guide" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">会话桥接</p>
              <h3>为什么登录态会影响业务区操作</h3>
            </div>
          </div>

          <ul class="list-dense">
            <li>本模板不自建账号体系，业务区只消费 Hub 会话。</li>
            <li>会话失效时会停止提交和轮询，避免把鉴权问题误算成任务失败。</li>
            <li>如果你在本地联调，可根据环境开关决定是否允许开发身份回退。</li>
          </ul>
        </section>

        <section id="troubleshooting" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">故障排查</p>
              <h3>常见失败与处理办法</h3>
            </div>
          </div>

          <div class="stack gap-4">
            <article class="advanced-box stack gap-3">
              <strong>会话失效</strong>
              <p class="muted">现象：顶部出现危险横幅，提交与刷新停止。</p>
              <p class="muted">处理：先去登录会话页确认身份，再回到工作台继续。</p>
            </article>
            <article class="advanced-box stack gap-3">
              <strong>AI 超时重试</strong>
              <p class="muted">现象：横幅显示“系统正在重试”，任务仍未进入最终失败。</p>
              <p class="muted">处理：先等待重试结束；若频繁出现，再调整 AI 配置的超时参数或减少输入复杂度。</p>
            </article>
            <article class="advanced-box stack gap-3">
              <strong>最终失败</strong>
              <p class="muted">现象：任务状态变为失败，详情里可以看到最近一次尝试记录。</p>
              <p class="muted">处理：先检查业务输入是否明确、素材链接是否有效、AI 配置是否合适，再决定是否重试。</p>
            </article>
          </div>
        </section>

        <section id="faq" class="panel stack gap-4 guide-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">常见问题</p>
              <h3>高频问题</h3>
            </div>
          </div>

          <div class="stack gap-4 faq-list">
            <details v-for="item in faqItems" :key="item.question" class="advanced-box">
              <summary>{{ item.question }}</summary>
              <div class="details-body">
                <p class="muted">{{ item.answer }}</p>
              </div>
            </details>
          </div>
        </section>
      </div>
    </section>
  </main>
</template>
