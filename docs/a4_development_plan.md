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

### 阶段 1 实施记录 (2026-03-24 05:49:20 UTC)
- 已新增 `apps/backend/` FastAPI 后端骨架，包含 `api/routes`、`models`、`repositories`、`services`、`workers`、`db` 等目录。
- 已实现五张核心业务表对应 SQLAlchemy 模型：`service_job`、`service_job_attempt`、`service_result`、`service_artifact`、`service_ai_profile`。
- 已实现任务状态机与 orchestrator：支持 `queued -> running -> succeeded | failed | review_required`，并覆盖幂等键、Provider 超时重试、限流重试、失败归类、结果落库。
- 已实现 `MockProviderAdapter`，统一封装 `prepare_request`、`invoke`、`normalize_response`，便于后续替换真实 Provider。
- 已实现任务接口、AI Profile 接口与 `/healthz`：
  - `POST /api/tasks`
  - `GET /api/tasks`
  - `GET /api/tasks/{job_id}`
  - `POST /api/tasks/{job_id}/retry`
  - `GET /api/settings/ai-profiles`
  - `POST /api/settings/ai-profiles`
  - `GET /healthz`
- 已实现内存队列版 worker、启动自动注册骨架、心跳降级标记和默认 AI Profile 引导数据。
- 已新增 `pyproject.toml` 固化运行与测试依赖，并补充 `tests/` 集成测试用例覆盖任务成功、超时失败、`/healthz` 降级场景。
- 当前阻塞项：本地 `pip install -e '.[dev]'` 受到外部包源摘要/索引异常影响，依赖尚未完成安装，因此集成测试尚未实际跑通；已完成 `python3 -m compileall apps/backend` 语法级检查。

## 阶段 2: 业务前端界面与组件实现 (Vue 3)
- **目标**: 实现 Vue 3 业务页面、交互组件和与后端 API 的联动。
- **Agent 执行步骤**:
  1. **组件与页面骨架生成 (Component Scaffolding)**: 按工程方案初始化页面结构，至少落实 `ServiceDashboardView`、`ServiceStatusBanner`、`TaskCreateCard`、`TaskListCard`、`TaskDetailDrawer`、`AiProfileDrawer`。
  2. **样式规范落地 (Design Tokens Alignment)**: 严格遵循 `DESIGN.md` 中定义的 spacing scale、主辅色、语义色和过渡时长，复用全局 Tokens，禁止自行引入杂乱风格或任意色值。
  3. **前端状态流与 API 互通 (State & HTTP Calling)**: 实现与工程方案对齐的状态管理，至少覆盖 `useHubSessionStore`、`useTaskStore`、`useAiProfileStore`、`useHealthStore` 对应职责。
  4. **容错与重定向逻辑 (Fallback & Redirection)**: 严格按 `docs/design/service_design_guidelines.md` 补齐未登录跳转、AI 调用超时分层降级、接口断联、空状态、失败原因展示和 `review_required` 中性提示。

### 阶段 2 实施记录 (2026-03-24 06:12:53 UTC)
- 已新增 `apps/frontend/` Vue 3 + Vite + TypeScript 前端工程，补齐 `package.json`、`tsconfig`、`vite.config.ts`、`index.html` 与基础样式入口。
- 已实现页面级容器与主组件树：
  - `ServiceDashboardView`
  - `ServiceStatusBanner`
  - `TaskCreateCard`
  - `TaskListCard`
  - `TaskDetailDrawer`
  - `AiProfileDrawer`
- 已实现与工程方案对齐的前端状态流：
  - `useHubSessionStore`：统一消费 Hub 会话注入、输出鉴权请求头并处理 `AUTH_REQUIRED/401/403` 登录失效跳转。
  - `useTaskStore`：覆盖任务创建、列表查询、详情查询、重试、轮询与最近成功数据保留策略。
  - `useAiProfileStore`：覆盖 AI Profile 列表读取、草稿保留、抽屉编辑和保存失败不丢稿。
  - `useHealthStore`：覆盖 `/healthz` 摘要拉取与顶部状态条展示。
- 已实现前后端 API 客户端与类型定义，对接：
  - `GET /healthz`
  - `GET /api/tasks`
  - `POST /api/tasks`
  - `GET /api/tasks/{job_id}`
  - `POST /api/tasks/{job_id}/retry`
  - `GET /api/settings/ai-profiles`
  - `POST /api/settings/ai-profiles`
- 已按 `DESIGN.md` 落地业务区 token：统一 spacing scale、蓝/灰主辅色、`success/warning/danger` 语义色、`150/200/300ms` 过渡时长、抽屉进场动画与 `prefers-reduced-motion` 降级。
- 已按 `docs/design/service_design_guidelines.md` 落地关键容错交互：
  - 未登录时停止业务操作并触发 Hub 登录跳转，不自建登录页。
  - AI 超时重试中显示顶部警告横幅并保持结果区加载态。
  - 表单校验失败显示字段级提示并聚焦首个错误字段。
  - `review_required` 独立使用中性/警告语义，不复用失败态。
- 已完成本地前端验证：
  - `npm install`
  - `npm run typecheck`
  - `npm run build`

## 阶段 3: 本地编译、联调验证与依赖清理 (Integration Checkout)
- **目标**: 确保新增代码在语法、类型、运行时和工程方案对齐上均无明显缺陷。
- **Agent 执行步骤**:
  1. **后端验证**: 运行格式化、静态检查和后端测试，确保模型、路由、worker、注册流可正常加载。
  2. **前端验证**: 运行类型检查、Lint 和前端构建，确保页面、状态流、API 调用无明显错误。
  3. **工程方案对齐验证**: 逐项核对是否已落实 `docs/architecture/service_engineering_plan.md` 中的四类关键内容：核心表结构、AI 编排骨架、`/healthz` 与注册流、前端组件树；并补测未登录拦截、AI 超时降级、表单校验首错聚焦三个关键交互。
  4. **错误反馈与自动修复循环 (Fix Loop)**: 若发现缺失模块、类型问题、协议不一致或实现偏离工程方案，必须先定位根因，再修改并复验。
  5. **阶段完成与交付 (Exit Criteria)**: 只有当本地检查通过、服务可启动、关键实现与 `docs/architecture/service_engineering_plan.md` 对齐时，A-4 阶段才算完成。

### 阶段 3 实施记录 (2026-03-24 06:48:00 UTC)
- 已补齐本地检查链路：
  - 后端新增 `ruff` 开发依赖与配置，完成 `ruff format --check`、`ruff check`、`pytest` 本地验证。
  - 前端新增 ESLint 平台、`npm run lint` / `npm run lint:fix` 脚本与 Vue SFC 解析配置，完成 `npm run typecheck`、`npm run lint`、`npm run build` 本地验证。
  - 新增 `.gitignore`，忽略 `.venv`、`__pycache__`、`.pytest_cache`、前端 `node_modules/dist` 等本地生成物，避免依赖产物污染工作树。
- 已修复阶段 3 暴露的真实问题：
  - 修复任务在 `timeout_once` 后重试成功时仍残留 `PROVIDER_TIMEOUT_RETRYING` 错误码的问题，避免前端误判为持续降级。
  - 收敛前端未登录拦截逻辑：会话失效时统一停止轮询、清空任务与健康摘要敏感运行态，并保留 AI Profile 草稿。
  - 收紧 AI 超时降级提示：仅在 `status=running` 且 `error_code=PROVIDER_TIMEOUT_RETRYING` 时展示顶部重试横幅，并显示当前尝试次数。
  - 补强表单校验汇总提示，与字段级报错和首错聚焦形成一致反馈。
- 已补回归验证：
  - 新增后端测试覆盖 `timeout_once` 场景，确认重试成功后不会保留陈旧错误码。
  - 新增未登录访问任务接口返回 `AUTH_REQUIRED` 的测试，确认前后端拦截协议一致。
- 已完成服务启动验证：
  - 使用 `.venv/bin/python -m uvicorn apps.backend.main:app --host 127.0.0.1 --port 8010` 启动本地服务。
  - 访问 `GET /healthz` 返回 `200 degraded`，其中 `database/queue/provider_adapter=healthy`、`hub_registration=degraded`，与工程方案中“Hub 断联时返回 degraded 而非误报实例死亡”的要求一致。
- 环境说明：
  - 由于系统 Python 启用了 PEP 668，`pip install -e '.[dev]'` 不能直接写入全局环境；阶段 3 已改为使用仓库内 `.venv` 执行后端依赖安装与验证。

### 阶段 3 补充联调与 QA 记录 (2026-03-24 08:30:00 UTC)
- 已按 `docs/auto_template_implementation_manual.md` 的 A-5 要求，对运行中的后端 `http://127.0.0.1:8000` 与前端 `http://127.0.0.1:4173` 执行系统性联调 QA，报告归档至 `docs/qa/service_qa_report.md`。
- 本轮 QA 首次暴露并确认 3 个真实联调缺陷：
  - 后端未配置 CORS，导致前端开发服务器对 `/healthz`、`/api/tasks`、`/api/settings/ai-profiles` 的真实请求被浏览器拦截。
  - 前端 `TaskCreateCard` 默认提交的 `input_payload.brief` 未被 mock provider 消费，结果预览回退为固定文案，业务输入未进入 AI 结果闭环。
  - `TaskDetailDrawer` 的加载态占位实际不可见，因为详情抽屉在接口返回前并不会打开。
- 已完成对应修复并补回归验证：
  - 后端新增 CORS 中间件，允许本地前端常用 origin 与任务请求头。
  - mock provider 增加对 `brief` 字段的兼容，前端表单默认载荷可直接参与结果生成。
  - 详情加载流改为“先开抽屉再请求详情”，并补充详情错误提示。
  - 后端新增回归测试覆盖前端形态 payload 与 CORS preflight，`pytest tests/test_tasks.py` 通过。
- 最终联调结果：
  - `/healthz` 返回 `200 degraded`，并包含 `database/queue/hub_registration/provider_adapter` 与 `queued_jobs/running_jobs/failed_jobs_10m`。
  - 无凭证访问前端时会展示失效横幅并自动跳转到配置登录地址；无凭证访问任务接口仍返回 `401 AUTH_REQUIRED`。
  - 顶部服务摘要、任务列表与任务详情的加载态均可见；空状态与 AI 配置抽屉默认配置加载正常。
  - 浏览器侧已验证任务创建后列表与详情联动正常，结果预览使用 `brief` 内容，不再退化为 `generated result`。

### 归档前服务审查记录 (2026-03-24 08:58:00 UTC)
- 已按“异常处理与重试机制 / Hub 状态透传 / 日志完整度”三项要求完成独立审查，结论文档归档至 `docs/reviews/service_review.md`。
- 已在本轮审查中修复 3 个高优问题：
  - Orchestrator 现在会按 `service_ai_profile.timeout_ms` 强制截断外部 Provider 调用，不再依赖 Provider 自行超时。
  - `asyncio.wait_for` 触发的超时现在会正确回写 `service_job_attempt.status=timeout`，避免任务详情时间线残留 `running`。
  - 已补齐任务提交、Provider 尝试、重试失败、Worker 队列、Hub 注册与基础异常处理日志。
- 已补额外回归：
  - `pytest tests/test_tasks.py` 新增 profile 级超时控制与 AI 配置接口鉴权覆盖，并已通过。
- 当前剩余关注项：
  - 后端对 Hub 登录态仍是“信任明文身份头”模式，尚未形成签名 / token / introspection 级别的真实会话校验闭环；该风险已在审查文档中明确标注，归档时需一并说明。

### 阶段 3 补充 IP 启动修复记录 (2026-03-25 08:18:00 UTC)
- 本轮按“必须通过 `IP + 端口` 访问服务，而不是 `localhost`”的要求复验了启动链路。
- 已定位并修复 2 个会影响 IP 访问的真实问题：
  - 前端 `apps/frontend/src/lib/api.ts` 默认将 API 基地址写死为 `http://localhost:8000`，导致页面从 `http://<server-ip>:5173` 打开时，浏览器仍会错误请求 `localhost:8000`。
  - 后端默认 CORS 仅放行 `localhost/127.0.0.1`，来自 `http://<server-ip>:5173` 的真实预检请求会被拦截。
- 已完成对应修复：
  - 前端默认 API 地址改为跟随当前访问页主机名，并保留 `VITE_API_BASE_URL` 显式覆盖能力。
  - 后端新增 `cors_allowed_origin_regex` 默认规则，允许 `localhost`、`127.0.0.1`、局域网 IPv4 与 IPv6 开发来源访问。
  - 新增回归测试 `test_cors_preflight_allows_ip_frontend_origin`，防止 IP 访问场景再次退化。
- 已完成复验：
  - `./.venv/bin/python -m pytest tests/test_tasks.py` 通过，`10 passed`。
  - `cd apps/frontend && npm run build` 通过。
  - 后端已用 `SERVICE_PUBLIC_BASE_URL=http://192.168.1.242:8000 ./.venv/bin/python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000` 成功启动。
  - 前端已用 `npm run dev -- --host 0.0.0.0 --port 5173` 成功启动，Vite 输出 `Network: http://192.168.1.242:5173/`。
  - 实测 `curl http://192.168.1.242:8000/healthz` 返回 `200 degraded`，`curl -I http://192.168.1.242:5173` 返回 `200 OK`，IP 来源的 CORS 预检返回 `access-control-allow-origin: http://192.168.1.242:5173`。

### 根目录启动脚本补充记录 (2026-03-25 08:22:00 UTC)
- 已在仓库根目录新增 `start.sh`，用于按 `IP + 端口` 一键同时启动后端与前端。
- 脚本行为：
  - 自动检测当前机器 IPv4 地址，也支持通过 `SERVICE_HOST_IP` 手动覆盖。
  - 自动导出 `SERVICE_PUBLIC_BASE_URL` 与 `VITE_API_BASE_URL`，避免前后端仍落回 `localhost`。
  - 以后端 `8000`、前端 `5173` 为默认端口，并在 `Ctrl+C` 时一并清理两个子进程。

### 登录校验开关补充记录 (2026-03-25 08:28:00 UTC)
- 已将 Hub 登录校验改为显式开关控制，当前默认关闭，便于本地直接启动和联调。
- 后端新增配置：
  - `REQUIRE_HUB_AUTH=false` 时，`get_auth_context` 会回退到本地开发身份，不再因缺失 `X-Hub-*` 请求头返回 `401 AUTH_REQUIRED`。
  - 重新开启时仅需设置 `REQUIRE_HUB_AUTH=true`。
- 前端新增配置：
  - `VITE_REQUIRE_HUB_AUTH=false` 时，不再因为缺失 Hub 注入会话而立即展示失效横幅并跳转登录页。
  - 重新开启时仅需设置 `VITE_REQUIRE_HUB_AUTH=true`。
- 根目录 `start.sh` 已同步桥接该开关：执行 `REQUIRE_HUB_AUTH=true ./start.sh` 时，会自动把 `VITE_REQUIRE_HUB_AUTH=true` 传给前端。
