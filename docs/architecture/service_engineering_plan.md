# 子服务工程实施计划
- 文档状态：Draft for Implementation
- 更新日期：2026-03-30
- 输入依据：`docs/PRD/service_prd.md`、`README.md`
- 适用范围：AI Auto Hub 体系下的单业务能力节点型子服务

## 1. 设计结论
本服务按 `任务提交 -> 异步执行 -> 结果沉淀 -> Hub 可治理` 的标准闭环设计。
当前 PRD 未锁定视频生成、内容生成或抓取中的具体方向，因此本方案采用领域中立模型：
- 本地只建设业务任务、结果、素材、AI 配置，不建设账号、RBAC、Hub 服务目录表。
- 所有用户信息均视为来自 Hub 的外部引用，只保存必要快照字段。
- 可变业务输入和输出采用 `jsonb` 承载，等具体业务收敛后再做字段下沉。

## 2. 推荐架构
当前推荐按 `ai-auto` 的多应用仓库方式拆分：
1. `apps/service-backend`：FastAPI 后端，负责 `/healthz` 与 `/api/v1/*` 业务接口。
2. `apps/service-worker`：独立 worker 进程，轮询数据库中的 `queued` 任务并执行编排。
3. `apps/service-frontend`：Vue 3 前端，使用 `router + pages + api + styles` 结构。
4. 正式环境默认使用平台共享网关统一承接 Hub 与各子服务；仓库内 `infra/nginx` + `docker-compose.yml` 仅保留为独立部署 fallback。
5. Hub Integration：由 backend 负责自动注册、心跳、探活和 Hub 上下文透传。
核心状态机：`draft -> queued -> running -> succeeded | failed | cancelled | review_required`
状态含义：
- `draft`：草稿或未通过校验。
- `queued`：已提交待执行。
- `running`：存在进行中的执行尝试。
- `succeeded`：结果已落库可回查。
- `failed`：重试耗尽或不可恢复错误。
- `cancelled`：用户或系统取消。
- `review_required`：技术成功但结果需要人工判断质量。

## 3. 本地数据库表结构设计
以下表仅覆盖本业务域，不包含全局账号表。

### 3.1 `service_job`
用途：任务主表，记录一次业务请求的完整生命周期。
主键与唯一键：`id uuid pk`，`job_no varchar(32) unique`
身份快照：`submitted_by_hub_user_id`，`submitted_by_name`，`source_channel`
业务字段：`scenario_key`，`title`，`ai_profile_id`
输入输出：`input_payload jsonb`，`normalized_payload jsonb`，`result_summary jsonb`
状态字段：`status`，`priority`，`current_attempt_no`
错误字段：`error_code`，`error_message`
时间字段：`started_at`，`finished_at`，`created_at`，`updated_at`
索引建议：`(status, created_at desc)`、`(submitted_by_hub_user_id, created_at desc)`、`gin(input_payload)`

### 3.2 `service_job_attempt`
用途：记录每次外部 AI 调用、重试和失败细节。
主键与约束：`id uuid pk`，`unique(job_id, attempt_no)`
关联字段：`job_id`，`attempt_no`，`workflow_stage`
Provider 字段：`provider_name`，`provider_model`，`external_request_id`
请求响应快照：`request_payload_masked jsonb`，`response_payload_trimmed jsonb`
执行指标：`latency_ms`，`input_tokens`，`output_tokens`
状态错误：`status`，`retryable`，`error_code`，`error_message`
时间字段：`started_at`，`finished_at`
索引建议：`(job_id, attempt_no desc)`

### 3.3 `service_result`
用途：沉淀结构化结果，支持重跑版本和人工复核。
主键：`id uuid pk`
关联字段：`job_id`
结果字段：`version_no`，`result_type`，`structured_payload jsonb`，`preview_text`
复核字段：`quality_status`，`review_comment`
时间字段：`created_at`，`updated_at`
说明：同一 `job_id` 允许多版本结果，便于重跑覆盖和历史回查。

### 3.4 `service_artifact`
用途：统一管理输入素材、中间件和最终产物。
主键：`id uuid pk`
关联字段：`job_id`，`attempt_id`
归类字段：`artifact_role`，`storage_type`
存储字段：`uri`，`mime_type`，`size_bytes`，`checksum`
扩展字段：`metadata jsonb`
时间字段：`created_at`

### 3.5 `service_ai_profile`
用途：承载本服务 AI Settings Center 的本地配置。
主键与唯一键：`id uuid pk`，`profile_key varchar(64) unique`
适用范围：`profile_name`，`scenario_key`，`is_default`，`is_active`
模型字段：`provider_name`，`model_name`
提示词字段：`system_prompt`，`prompt_template`
参数字段：`temperature`，`max_tokens`，`timeout_ms`，`max_retries`，`concurrency_limit`
审计字段：`created_by_hub_user_id`，`updated_by_hub_user_id`
时间字段：`created_at`，`updated_at`

## 4. 外部 AI 接口调用逻辑与工作流编排
主流程：
1. 前端提交任务，后端完成参数校验、Hub 登录态校验和幂等键校验。
2. API 写入 `service_job`，状态置为 `queued`，不在请求线程内直接执行任务。
3. 独立 worker 进程轮询数据库中的 `queued` 任务，加载 `service_ai_profile`、业务输入和关联素材。
4. Orchestrator 执行四段式流程：`prepare -> invoke provider -> normalize result -> persist output`。
5. 每次外部调用都写入 `service_job_attempt`，记录 provider、耗时、token、错误和外部请求 ID。
6. 成功后写入 `service_result` 与 `service_artifact`，并回写 `service_job.status/result_summary`。
7. 前端通过轮询或 SSE 刷新状态；详情页聚合 `job + attempts + result + artifacts` 展示。
编排原则：
- Adapter 模式：统一 Provider 接口为 `prepare_request`、`invoke`、`normalize_response`。
- 超时重试：按 `service_ai_profile.timeout_ms` 控制，只有可重试错误进入指数退避。
- 幂等保护：建议使用 `submitted_by_hub_user_id + normalized_payload_hash + time_bucket` 生成业务幂等键。
- 错误分层：至少区分业务校验失败、Provider 超时、Provider 限流、后处理失败。
- 审计留痕：只保存脱敏请求摘要，不保存明文密钥。
状态与错误协议补充：
- 登录态失效时，任务接口和配置接口应返回 HTTP `401/403` 或业务码 `AUTH_REQUIRED`；前端收到后立即停止轮询、清空敏感内存态并跳转 Hub 登录。
- Provider 单次超时但仍可重试时，任务详情应返回 `status=running`，并附带 `error_code=PROVIDER_TIMEOUT_RETRYING`、`current_attempt_no`、`max_retries`。
- Provider 超时且重试耗尽时，任务详情应返回 `status=failed`，并附带 `error_code=PROVIDER_TIMEOUT_FINAL`、`retryable=true` 和面向用户的 `error_message`。
- 表单或业务校验失败时，创建接口应返回 `VALIDATION_ERROR` 和 `field_errors`，其中 `field_errors` 必须可直接映射到前端字段组件。
- `review_required` 必须作为独立业务状态返回，不得复用 `failed` 或以空结果代替。
推荐模块拆分：
- `apps/service-backend/app/api/routes/tasks.py`
- `apps/service-backend/app/api/routes/settings.py`
- `apps/service-backend/app/api/routes/ops.py`
- `apps/service-backend/app/api/router.py`
- `apps/service-backend/app/services/orchestrator.py`
- `apps/service-backend/app/services/providers/base.py`
- `apps/service-backend/app/services/providers/*.py`
- `apps/service-backend/app/workers/job_worker.py`
- `apps/service-backend/app/workers/monitor.py`
- `apps/service-backend/app/models/*.py`
- `apps/service-worker/service_worker/main.py`

## 5. `/healthz` 接口设计与自动注册流预设计
`/healthz` 设计：
- 方法：`GET /healthz`
- 用途：供 Hub Worker、容器平台、负载均衡器统一探活。
- HTTP 语义：`200` 表示 `healthy/degraded`，`503` 表示 `unhealthy`。
- 响应建议包含：`status`、`service`、`version`、`instance_id`、`uptime_sec`、`checks`、`metrics`、`timestamp`
- `checks` 至少包含：`database`、`queue`、`hub_registration`、`provider_adapter`
- `metrics` 至少包含：`queued_jobs`、`running_jobs`、`failed_jobs_10m`
- 判定规则：数据库失败直接返回 `503`；队列或外部 AI 短时异常返回 `200 + degraded`
- 性能要求：只做轻量检查，不跑重 SQL，目标耗时小于 300ms
自动注册流：
1. 启动时读取 `SERVICE_BACKEND_HUB_API_URL`、`SERVICE_BACKEND_HUB_SERVICE_KEY`、`SERVICE_BACKEND_SERVICE_PUBLIC_BASE_URL`、`SERVICE_BACKEND_APP_VERSION`、`SERVICE_BACKEND_SERVICE_CAPABILITIES`。
2. 本地自检数据库、worker、`/healthz` 是否可用。
3. 向 Hub 内部注册接口发起请求，建议路径为 `POST /internal/services/register`。
4. 注册载荷至少包含：`service_key`、`display_name`、`description`、`version`、`base_url`、`healthz_url`、`team`、`environment`、`capabilities`、`instance_id`。
5. Hub 返回 `registration_id` 和租约 TTL；本地定时任务按 `TTL/2` 周期发送心跳。
6. 心跳附带摘要指标：运行中任务数、失败任务数、最近错误摘要、版本号。
7. 注册或心跳失败时采用指数退避，不阻塞服务启动；同时将 `/healthz.checks.hub_registration` 置为 `degraded`。
8. 进程退出时最佳努力发起反注册，失败则由 Hub 侧按租约过期回收。

## 6. 本地前端组件树拆解
页面级容器改为与 `ai-auto` 一致的路由结构：
- `src/App.vue`：统一侧栏、顶部工作区标题和会话区
- `src/router/index.ts`
- `src/pages/DashboardPage.vue`
- `src/pages/WorkbenchPage.vue`
- `src/pages/ProfilesPage.vue`
- `src/pages/LoginPage.vue`

业务组件保持模板职责：
- `ServiceStatusBanner`
- `TaskCreateCard`
- `TaskListCard`
- `TaskDetailDrawer`
- `AiProfileDrawer`
局部组件树：
- `TaskCreateCard`：`ScenarioSelector`、`BusinessInputForm`、`AssetUploader`、`AdvancedOptionsCollapse`、`SubmitActionBar`
- `TaskListCard`：`TaskFilterBar`、`TaskTable`、`TaskStatusBadge`、`TaskPagination`
- `TaskDetailDrawer`：`TaskMetaPanel`、`ExecutionTimeline`、`ResultPreviewPanel`、`ArtifactList`、`FailureReasonPanel`
- `AiProfileDrawer`：`ProfileSelector`、`PromptEditor`、`ModelParamsForm`、`SaveProfileBar`
- `ServiceStatusBanner`：展示 Hub 继承登录态、服务健康摘要、队列摘要和注册状态提示
前端状态建议：
- `useHubSessionStore`：只读消费 Hub 注入的登录态和角色
- `useTaskStore`：任务创建、列表、详情、轮询和重试
- `useAiProfileStore`：AI 配置读取、保存和默认项切换
- `useHealthStore`：`/healthz` 摘要和注册状态
前端行为约束：
- `useHubSessionStore` 必须提供统一的未登录拦截处理入口，避免每个页面各写一次跳转逻辑。
- `useTaskStore` 必须显式区分 `loading`、`retrying`、`failed`、`review_required`，不能只保留一个布尔型 `isLoading`。
- `useTaskStore` 在轮询失败时应保留最近一次成功数据，不得将列表整体清空。
- `useAiProfileStore` 在保存失败或会话失效时必须保留用户未提交修改。
- `ServiceStatusBanner` 只展示业务区顶部状态，不接管 Hub 全局通知中心。

## 7. 实施顺序与验证重点
实施顺序：
1. 先落五张核心表和迁移脚本。
2. 再完成任务 API、worker、provider adapter、状态机流转。
3. 然后补 `/healthz`、自动注册、心跳上报。
4. 最后实现前端任务页、详情抽屉、AI 配置抽屉。
验证重点：
- 重复提交是否被幂等策略拦截。
- 外部 AI 超时后是否正确重试并写清失败原因。
- `/healthz` 在 Hub 断联时是否返回 `degraded` 而不是误报实例死亡。
- 详情页是否完整展示结果、素材和执行轨迹。
- Hub 未登录拦截时，业务区是否进入只读阻断态，并在不中断 Hub Shell 的前提下触发登录跳转。
- 表单校验失败时，是否同时出现字段提示、汇总提示和首错聚焦。
- `review_required` 是否与 `failed` 在状态文案、色彩和默认操作上明确区分。
