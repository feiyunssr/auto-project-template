# 服务模块归档前独立审查
- 审查时间：2026-03-24
- 审查范围：`apps/backend/services/*`、`apps/backend/api/routes/*`、`apps/backend/workers/*`、`apps/frontend/src/stores/*`
- 审查重点：
  1. 异常处理与重试机制，尤其是外部 AI 调用。
  2. 页面请求是否正确携带并透传 Hub 状态。
  3. 日志完整度。

## 结论
状态：`DONE_WITH_CONCERNS`

本轮发现 4 个重要结论，其中 3 个已修复，1 个为归档前必须知晓的剩余风险。

## 发现与处理
### 1. 高优已修复：外部 AI 调用未真正受 `timeout_ms` 控制
- 位置：`apps/backend/services/orchestrator.py`
- 问题：原实现只依赖 Provider 主动抛出 `ProviderTimeoutError`。如果真实外部 AI 请求 hang 住，编排层不会按 `service_ai_profile.timeout_ms` 截断，重试链路也不会启动。
- 处理：已在编排层对 `provider.invoke(...)` 增加 `asyncio.wait_for(...)`，统一按 profile 的 `timeout_ms` 触发超时，并保持后续错误归类与重试逻辑一致。
- 回归：新增 `test_profile_timeout_ms_enforces_provider_call_deadline`。

### 2. 高优已修复：框架级超时会把 attempt 留在 `running`
- 位置：`apps/backend/services/orchestrator.py`
- 问题：在引入 `wait_for` 后，如果是框架层抛出的 `asyncio.TimeoutError`，任务主状态会失败，但 `service_job_attempt.status` 可能仍停留在 `running`，导致详情时间线与真实执行结果不一致。
- 处理：已在超时分支内显式写回 `attempt.status=timeout`、`error_code=PROVIDER_TIMEOUT`、`finished_at` 后再抛出统一错误。
- 回归：同一超时测试已覆盖 attempt 状态。

### 3. 高优已修复：关键链路日志几乎为空
- 位置：`apps/backend/main.py`、`apps/backend/api/routes/tasks.py`、`apps/backend/api/routes/settings.py`、`apps/backend/services/orchestrator.py`、`apps/backend/services/registration.py`、`apps/backend/workers/job_worker.py`
- 问题：提交任务、Provider 尝试、重试、最终失败、Worker 入队/出队、Hub 注册失败等关键事件此前没有结构化日志，线上排障和 Hub 聚合诊断都缺证据。
- 处理：已补基础 logging 配置，并覆盖以下事件：
  - 服务启动与停止
  - 任务创建、幂等命中、重试入队
  - Provider attempt 开始、可重试错误、任务成功、任务失败
  - Worker 启停、入队、出队
  - Hub 注册关闭、注册失败、注册成功、心跳成功
  - 业务异常和请求校验异常

### 4. 重要剩余风险：后端仍然信任明文 Hub 头，不验证签名或会话真实性
- 位置：`apps/backend/api/dependencies.py`
- 现状：后端只校验 `x-hub-user-id` 是否存在，即视为登录态成立；没有和 Hub 做签名、token、session introspection 或网关级校验。
- 影响：这意味着“页面调用携带了 Hub 状态”在当前实现里更接近“携带了 Hub 身份快照”，而不是真正经过验证的 Hub 会话。前端本轮已修复为会话失效后不再继续发送旧头，但服务端仍缺少强校验闭环。
- 建议：归档前至少补齐以下其一：
  - 由 Hub 网关注入并校验不可伪造的身份头；
  - 改为 Bearer token / session ticket，并在子服务后端校验；
  - 增加与 Hub 的 introspection 接口约定。

## Hub 状态透传核对结果
- 已核对页面请求路径：
  - 首屏：`/healthz`、`/api/tasks`、`/api/settings/ai-profiles`
  - 明细：`/api/tasks/{job_id}`
  - 操作：`POST /api/tasks`、`POST /api/tasks/{job_id}/retry`、`POST /api/settings/ai-profiles`
- 结论：
  - 正常路径下，前端 store 均通过 `useHubSessionStore.authHeaders()` 统一附带 Hub 头。
  - 本轮已修复 `authExpired=true` 时仍可能继续生成旧头的问题，避免失效会话在页面侧继续透传。
  - `/healthz` 后端按基础设施探活设计不强制鉴权，这一点与任务/配置接口不同，属于预期差异，不算漏传。

## 验证记录
- `.venv/bin/pytest tests/test_tasks.py`
- `.venv/bin/ruff check apps/backend tests`
- `cd apps/frontend && npm run typecheck`

## 归档建议
- 可以进入归档，但应把“Hub 头当前仅是身份快照、不是已验证会话”作为显式风险写入归档说明，避免后续误判为已完成真正的 Hub SSO 闭环。
