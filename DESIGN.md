# AI Auto Hub 子服务设计系统对齐说明
- 文档状态：Reviewed
- 更新日期：2026-03-27
- 对齐基准：`/home/zero/external-cortex/Zero/ai-auto`
- 作用范围：模板默认独立运行时的完整外壳与业务区视觉；嵌入 Hub 后也必须保持同一套 token 与状态语义

## 1. 设计目标
`auto-project-template` 必须以 `ai-auto` 为唯一视觉基线，不再维护一套独立的浅色业务页风格。

硬约束：
- 默认使用与 `ai-auto` 一致的深色控制台底色、玻璃化面板、柔和渐变背景。
- 侧栏、顶栏、业务卡片、抽屉、状态横幅都沿用同一层级逻辑。
- 子服务可以替换业务内容，但不能替换整套视觉气质。
- 本模板独立运行时，由模板自己渲染 Hub-style shell；嵌入真实 Hub 后，也不得再切回另一套样式体系。

## 2. 核心视觉 Token
```css
:root {
  color-scheme: dark;
  --bg-base: #0b0f19;
  --bg-panel: rgba(255, 255, 255, 0.04);
  --bg-panel-hover: rgba(255, 255, 255, 0.07);
  --border-subtle: rgba(255, 255, 255, 0.1);
  --text-main: #e2e8f0;
  --text-muted: #94a3b8;
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --neutral: #64748b;
  --shadow-panel: 0 18px 48px rgba(0, 0, 0, 0.35);
}
```

补充规则：
- 字体优先 `Inter, Outfit, sans-serif`。
- 页面底色使用与 `ai-auto` 同类的双径向渐变 + 深色纵向渐变，不得回退为纯白或纯灰。
- 面板 hover 只做轻微亮度抬升，不引入彩虹阴影、霓虹描边或高饱和装饰色。

## 3. 布局规则
### 3.1 外壳结构
- 左侧固定侧栏宽度 `240px`。
- 主内容区包含顶部标题栏和最大宽度内容容器。
- 移动端下侧栏收敛为顶部区块，保持同一视觉 token。

### 3.2 业务区结构
- 首屏先显示 hero 区，再显示服务状态横幅和主工作区。
- 任务创建卡与任务列表卡并排；窄屏下改为单列。
- 抽屉始终从右侧滑入，遮罩为深色半透明，不允许使用浅色 modal。

## 4. 组件级对齐要求
### 4.1 面板与卡片
- 卡片、抽屉、状态面板统一使用 `border + blur + shadow-panel`。
- 圆角以 `12px-18px` 为主，不使用大面积 `rounded-full`。
- 空状态和错误态也必须留在面板体系内，不切换成另一套页面骨架。

### 4.2 按钮
- 主按钮使用 `primary -> primary-hover` 渐变。
- 次按钮使用半透明深色底 + 细描边。
- 文本按钮只作为低优先级操作，不承担主流程提交。

### 4.3 状态语义
- `healthy/succeeded` 使用 `success`。
- `degraded/review_required/running timeout retrying` 使用 `warning`。
- `failed/auth expired` 使用 `danger`。
- 中性状态使用 `neutral`，禁止把待复核与失败混为一类。

### 4.4 表单与表格
- 输入框背景为深色半透明，不允许回到浅色表单控件。
- focus ring 使用主色低透明发光。
- 表格边框和分割线统一使用 `border-subtle`，说明文字使用 `text-muted`。

## 5. 模板实现边界
模板不是 Hub 本体，但必须长得像 Hub 家族：
- 独立运行时，模板负责渲染与 `ai-auto` 一致的 shell 占位。
- 接入真实 Hub 后，若外层壳由 Hub 接管，业务区仍沿用同一色板、按钮、状态 badge 和抽屉样式。
- 不允许同时存在“模板本地浅色版”和“接入 Hub 深色版”两套并行主题。

## 6. 验收清单
- 首屏能一眼看出与 `ai-auto` 属于同一产品家族。
- 不再出现白底业务页、蓝灰轻后台或另一套独立 token。
- 侧栏、顶栏、卡片、抽屉、横幅、状态 badge 都复用同一视觉语言。
- `TaskCreateCard`、`TaskListCard`、`TaskDetailDrawer`、`AiProfileDrawer` 的颜色、圆角、阴影和交互动效统一。
- `prefers-reduced-motion` 已降级，移动端布局不会破坏控制台层级。
