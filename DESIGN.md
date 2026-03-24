# AI Auto Hub 子服务视觉 Token 方案
- 文档状态：Reviewed
- 更新日期：2026-03-24
- 设计依据：`README.md`、`docs/design/service_design_guidelines.md`
- 作用范围：仅覆盖子服务业务区视觉 token 与交互动效；不覆盖 Hub Shell 的顶栏、侧栏、登录页和全局导航
## 1. 视觉落地边界
本方案只允许使用 AI Auto Hub 已有的 Tailwind-like 商务化视觉语言，不引入新的品牌色系、玻璃拟态、重渐变或高饱和装饰色。
- 主色只使用 `blue` 色阶，承担主按钮、激活态、链接和焦点环。
- 辅色只使用 `slate` 色阶，承担背景、卡片、分割线、正文和次级按钮。
- 语义色只使用 `emerald`、`amber`、`red` 三套标准色阶，分别对应成功、警告、失败。
- 禁止在业务区新增 `purple`、`pink`、霓虹渐变、彩虹阴影和无来源的任意十六进制颜色。
- 禁止大量使用 `rounded-full`、超大模糊阴影和长距离弹跳动画，避免和 Hub 既有控制台气质冲突。

## 2. 间距系统
采用 4px 基础网格，与 Tailwind-like spacing scale 对齐。除业务图表或素材预览外，不使用任意值间距。
```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --radius-sm: 0.5rem;
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
  --radius-xl: 1.25rem;
  --content-max: 80rem;
}
```
### 2.1 布局规则
- 页面内容容器：`max-w-[var(--content-max)] mx-auto px-6 py-6`，大屏可升到 `xl:px-8`
- 卡片外层堆叠：统一 `gap-6`
- 单张业务卡片内边距：桌面端 `p-6`，移动端 `p-5`
- 表单字段纵向间距：`gap-4`
- 单个字段的标题、说明、输入框、错误提示纵向间距：`gap-2`
- 卡片内分区之间：`gap-5`，分割线前后保留 `py-4`
- 列表行内边距：`px-5 py-4`
- 顶部状态横幅：`px-4 py-3`
- 抽屉正文：`px-6 py-6`，分区间距 `gap-6`
### 2.2 组件级约束
- `ServiceDashboardView`：业务区主列宽不超过 `80rem`，禁止铺满超宽屏。
- `TaskCreateCard` 与 `TaskListCard`：卡片结构一致，避免一张卡紧一张卡松。
- `TaskDetailDrawer`：桌面宽度 `w-[720px]`，移动端 `w-full`。
- `FailureReasonPanel`、`ServiceStatusBanner`：使用紧凑内边距 `p-4`，不做厚重告警盒子。
- 表单提交区按钮组：主次按钮间距 `gap-3`，禁止塞满整行。

## 3. 配色系统
### 3.1 固定色板
只使用 Tailwind-like 标准色阶，下面的 token 为默认值，不允许自行替换为新的品牌色。
```css
:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-muted: #f1f5f9;
  --color-border: #cbd5e1;
  --color-border-strong: #94a3b8;
  --color-text: #0f172a;
  --color-text-muted: #475569;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-soft: #dbeafe;
  --color-success: #059669;
  --color-success-soft: #d1fae5;
  --color-warning: #d97706;
  --color-warning-soft: #fef3c7;
  --color-danger: #dc2626;
  --color-danger-soft: #fee2e2;
}

.dark {
  --color-bg: #020617;
  --color-surface: #0f172a;
  --color-surface-muted: #1e293b;
  --color-border: #334155;
  --color-border-strong: #475569;
  --color-text: #e2e8f0;
  --color-text-muted: #94a3b8;
  --color-primary: #3b82f6;
  --color-primary-hover: #60a5fa;
  --color-primary-soft: #1e3a8a;
  --color-success: #10b981;
  --color-success-soft: #064e3b;
  --color-warning: #f59e0b;
  --color-warning-soft: #78350f;
  --color-danger: #ef4444;
  --color-danger-soft: #7f1d1d;
}
```
### 3.2 主辅色分层
- 主色 `primary`：只用于主按钮、当前激活标签、文本链接、focus ring、可点击状态强调。
- 辅色 `slate`：用于页面底、卡片底、边框、说明文字、禁用态和次级按钮。
- 成功 `emerald`：仅用于成功状态、健康状态、已完成任务。
- 警告 `amber`：仅用于超时重试中、待确认、轻量阻断提示。
- 失败 `red`：仅用于认证失效、最终失败、删除确认等高风险语义。
### 3.3 使用禁区
- 加载态骨架、占位区和空态插图背景只能使用 `surface-muted`，不能染成主色块。
- `review_required` 必须使用 `warning` 或中性 `slate`，不得复用失败红色。
- 顶部未登录横幅使用 `danger-soft + danger`，任务自动重试横幅使用 `warning-soft + warning`。
- 次级按钮只允许 `surface/surface-muted + border + text` 组合，不做彩色描边按钮。

## 4. 过渡动画系统
动效目标是让业务状态变化可感知，但不抢戏。统一使用短时长、低位移、可降级的 Tailwind-like 过渡。
```css
:root {
  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-emphasis: cubic-bezier(0.2, 0, 0, 1);
  --ease-exit: cubic-bezier(0.4, 0, 1, 1);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 1ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 1ms !important;
  }
}
```
### 4.1 统一规则
- 按钮 hover、边框高亮、文字颜色变化：`duration-fast`
- 输入框 focus ring、错误态切换、标签激活态：`duration-fast`
- 卡片阴影、背景色和轻微位移：`duration-base`
- 抽屉进出场、遮罩透明度变化：`duration-slow`
- 页面首屏模块出现不做级联大动画，只允许 `opacity + translateY(4px)` 的轻量进入
### 4.2 组件动效约束
- `TaskCreateCard` 提交后：按钮切到 loading，透明度和文案切换使用 `duration-fast`
- `TaskListCard` 行状态刷新：仅局部徽标和辅文案淡入，不整体闪烁重绘
- `TaskDetailDrawer`：使用 `translateX(16px) -> 0` + `opacity`，总时长 `300ms`
- `ServiceStatusBanner`：顶部横幅使用 `opacity` + `translateY(-4px)`，总时长 `200ms`
- 骨架屏 shimmer：`1200ms linear infinite`，仅用于等待态，不用于失败或空态

## 5. 代码映射方式
### 5.1 CSS 变量与 Tailwind-like 主题扩展
```ts
export const theme = {
  extend: {
    colors: {
      hub: {
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        muted: "var(--color-surface-muted)",
        border: "var(--color-border)",
        borderStrong: "var(--color-border-strong)",
        text: "var(--color-text)",
        textMuted: "var(--color-text-muted)",
        primary: "var(--color-primary)",
        primaryHover: "var(--color-primary-hover)",
        primarySoft: "var(--color-primary-soft)",
        success: "var(--color-success)",
        successSoft: "var(--color-success-soft)",
        warning: "var(--color-warning)",
        warningSoft: "var(--color-warning-soft)",
        danger: "var(--color-danger)",
        dangerSoft: "var(--color-danger-soft)"
      }
    },
    borderRadius: {
      sm: "var(--radius-sm)",
      md: "var(--radius-md)",
      lg: "var(--radius-lg)",
      xl: "var(--radius-xl)"
    },
    transitionDuration: {
      fast: "var(--duration-fast)",
      base: "var(--duration-base)",
      slow: "var(--duration-slow)"
    }
  }
};
```
### 5.2 组件 class 基线
- 卡片：`rounded-xl border border-hub-border bg-hub-surface px-6 py-5 shadow-sm`
- 主按钮：`bg-hub-primary text-white hover:bg-hub-primaryHover transition-colors duration-fast`
- 次按钮：`border border-hub-border bg-hub-surface text-hub-text hover:bg-hub-muted transition-colors duration-fast`
- 输入框：`border border-hub-border bg-hub-surface focus:border-hub-primary focus:ring-2 focus:ring-hub-primary/30`
- 危险横幅：`border border-hub-danger/20 bg-hub-dangerSoft text-hub-danger`
- 警告横幅：`border border-hub-warning/20 bg-hub-warningSoft text-hub-warning`

## 6. 与业务交互规则的对齐
- 未登录拦截：只改变业务区横幅、遮罩和按钮状态，不创建新的登录配色体系。
- AI 超时重试中：沿用 `warning` 体系，保留骨架屏和中性结果区背景。
- AI 最终失败：只在 `FailureReasonPanel` 等局部区域切换 `danger` 语义，不把整页刷红。
- 表单校验失败：字段描边、错误文案和汇总条共用 `danger` 体系，优先改变边框与文本，不加入震动动画。
- `review_required`：使用 `warningSoft` 或 `surface-muted`，显式区别于 `failed`。

## 7. 验收清单
- 页面所有颜色都能映射到本文 token，不出现零散任意色值。
- 页面布局只使用 4px 网格衍生 spacing，不出现无来源的大块留白或拥挤拼接。
- 交互动效统一落在 `150/200/300ms` 三档，不出现 500ms 以上拖沓动画。
- 已实现 `prefers-reduced-motion` 降级。
- `TaskCreateCard`、`TaskListCard`、`TaskDetailDrawer`、`AiProfileDrawer` 使用同一套卡片、边框、文字和状态 token。
