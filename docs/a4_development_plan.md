# 业务代码具体实现 (阶段 A-4) 开发计划文档

## 概述 (Overview)
本文档是基于 `docs/auto_template_implementation_manual.md` 中 **A-4. 业务代码具体实现** 环节扩展的详细 AI 代理开发计划。
进入本阶段前，前置文档必须已经收敛到 `docs/` 目录，尤其是 `docs/architecture/service_engineering_plan.md`。本文档的作用不是重新发明实现方案，而是把工程方案转成可执行的编码步骤。

## 实施基线 (Implementation Baseline)
- **唯一实施基线**: 本阶段所有技术实现必须以 `docs/architecture/service_engineering_plan.md` 为准。
- **严格落实范围**: 必须按工程方案落实核心表结构、任务状态机、AI 编排流程、`/healthz` 协议、Hub 自动注册流和前端组件树。
- **交互实现底线**: 必须同步落实未登录拦截、AI 超时三层降级、表单校验统一提示和 `review_required` 独立展示，禁止仅完成接口不完成状态反馈。
- **冲突处理原则**: 如果实现过程中发现 PRD、设计稿或临时想法与工程方案冲突，必须先更新 `docs/architecture/service_engineering_plan.md`，再继续编码，禁止绕过文档直接落代码。
- **最低完成标准**: 至少完成五张核心业务表、异步任务编排骨架、`/healthz` 与注册机制、前端主组件树和本地联调验证。

## 前提条件与上下文加载 (Context Anchor & Initialization)
- **目标**: 确保 Agent 完全理解本阶段的业务边界、工程约束和 Hub 集成要求。
- **Agent 执行步骤**:
  1. 完整读取 `docs/PRD/service_prd.md`、`docs/architecture/service_engineering_plan.md`、`docs/design/service_design_guidelines.md`、`DESIGN.md`，其中 `docs/architecture/service_engineering_plan.md` 是直接实施依据，`DESIGN.md` 是视觉 token 实施基线。
  2. 若页面交互、异常反馈或默认文案与实现发生冲突，必须以 `docs/design/service_design_guidelines.md` 中关于未登录拦截、AI 超时降级、表单校验提示的规定为准；若视觉样式、间距、主辅色或过渡动画发生冲突，必须以 `DESIGN.md` 为准，并先更新文档再改代码。
  3. 执行 `date` 获取当前时间，作为日志、版本信息和交付记录的时间戳。
  4. 启用目录保护策略（如 `/freeze`），将改动限制在业务专有目录，禁止修改全局 Auth、Hub Shell 和通用底座。

## 阶段 1: 业务后端与数据访问层实现 (FastAPI & Database)
- **目标**: 实现业务专属数据模型、FastAPI 路由、异步任务骨架和外部 AI 接口集成。
- **Agent 执行步骤**:
  1. **数据模型构建 (Data Modeling)**: 创建数据库模型和前后端交互协议，必须优先落实工程方案中的 `service_job`、`service_job_attempt`、`service_result`、`service_artifact`、`service_ai_profile` 五类核心实体。
  2. **状态机与编排骨架 (State Machine & Orchestration)**: 按工程方案实现任务状态机和四段式编排流程 `prepare -> invoke provider -> normalize result -> persist output`，并补齐幂等、超时、重试、失败归类。
  3. **核心业务与外部调用封装 (Core Logic Integration)**: 封装 Provider Adapter，统一处理鉴权、请求格式、响应归一化、异常捕获和脱敏日志。
  4. **探活与服务注册接口 (Healthz & Registration)**: 严格按工程方案暴露 `/healthz`，实现启动注册、心跳上报和降级状态标记，不得自行发明协议。
  5. **依赖检查与安装 (Dependency Check)**: 检查并安装所需第三方依赖，并将依赖固化到项目依赖文件。

## 阶段 2: 业务前端界面与组件实现 (Vue 3)
- **目标**: 实现 Vue 3 业务页面、交互组件和与后端 API 的联动。
- **Agent 执行步骤**:
  1. **组件与页面骨架生成 (Component Scaffolding)**: 按工程方案初始化页面结构，至少落实 `ServiceDashboardView`、`ServiceStatusBanner`、`TaskCreateCard`、`TaskListCard`、`TaskDetailDrawer`、`AiProfileDrawer`。
  2. **样式规范落地 (Design Tokens Alignment)**: 严格遵循 `DESIGN.md` 中定义的 spacing scale、主辅色、语义色和过渡时长，复用全局 Tokens，禁止自行引入杂乱风格或任意色值。
  3. **前端状态流与 API 互通 (State & HTTP Calling)**: 实现与工程方案对齐的状态管理，至少覆盖 `useHubSessionStore`、`useTaskStore`、`useAiProfileStore`、`useHealthStore` 对应职责。
  4. **容错与重定向逻辑 (Fallback & Redirection)**: 严格按 `docs/design/service_design_guidelines.md` 补齐未登录跳转、AI 调用超时分层降级、接口断联、空状态、失败原因展示和 `review_required` 中性提示。

## 阶段 3: 本地编译、联调验证与依赖清理 (Integration Checkout)
- **目标**: 确保新增代码在语法、类型、运行时和工程方案对齐上均无明显缺陷。
- **Agent 执行步骤**:
  1. **后端验证**: 运行格式化、静态检查和后端测试，确保模型、路由、worker、注册流可正常加载。
  2. **前端验证**: 运行类型检查、Lint 和前端构建，确保页面、状态流、API 调用无明显错误。
  3. **工程方案对齐验证**: 逐项核对是否已落实 `docs/architecture/service_engineering_plan.md` 中的四类关键内容：核心表结构、AI 编排骨架、`/healthz` 与注册流、前端组件树；并补测未登录拦截、AI 超时降级、表单校验首错聚焦三个关键交互。
  4. **错误反馈与自动修复循环 (Fix Loop)**: 若发现缺失模块、类型问题、协议不一致或实现偏离工程方案，必须先定位根因，再修改并复验。
  5. **阶段完成与交付 (Exit Criteria)**: 只有当本地检查通过、服务可启动、关键实现与 `docs/architecture/service_engineering_plan.md` 对齐时，A-4 阶段才算完成。
