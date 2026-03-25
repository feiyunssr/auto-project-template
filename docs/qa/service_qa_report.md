# 子服务联调 QA 报告

## 基本信息
- 执行时间：2026-03-24 UTC
- 测试目标：`http://127.0.0.1:8000` 后端接口 + `http://127.0.0.1:4173` 前端页面
- 执行范围：核心任务闭环、空态/加载态、访客重定向、`/healthz` 协议

## 本次发现并已修复的问题
1. 后端未配置 CORS，前端从 Vite 开发服务器访问 `/healthz`、`/api/tasks`、`/api/settings/ai-profiles` 时被浏览器直接拦截，导致真实前后台联动不可用。
2. 前端提交的 `input_payload.brief` 未被 mock provider 消费，任务虽然成功，但结果预览退化为固定的 `generated result`，核心 AI 输入没有进入结果闭环。
3. 任务详情抽屉在接口返回前不会打开，导致“任务详情加载中...”占位永远不可见，详情加载态名义存在、实际缺失。

## 修复摘要
- 后端新增 `CORSMiddleware`，放行本地前端开发常用 origin，并允许任务接口所需自定义请求头。
- mock provider 增加对 `input_payload.brief` 的兼容，前端默认表单结构可以直接进入结果生成链路。
- 详情加载流程调整为“先打开抽屉，再请求详情”，并补充详情错误消息渲染。
- 新增回归测试：
  - `test_frontend_shaped_payload_uses_brief_as_result_source`
  - `test_cors_preflight_allows_local_frontend_origin`

## 验证结果
### 1. 数据写入与核心 AI 接口流程闭环
- 通过 API 创建任务，任务可进入 `queued/running/succeeded` 完整流转。
- 幂等创建仍然有效：相同 payload 二次提交返回同一任务 ID。
- `timeout_once` 场景仍能重试成功，且不会残留陈旧错误码。
- 前端真实表单形态 `input_payload = { brief, asset_urls }` 现已正确生成结果：
  - 最终复验结果：`flash sale copy :: 784b037767e2f33f`
- 浏览器侧验证通过：页面提交后，任务标题出现在列表中，结果预览使用业务输入内容，不再回退为 `generated result`。

### 2. 空状态或加载中的渲染正确性
- 已验证顶部服务摘要加载文案可见：`正在加载服务健康摘要`
- 已验证任务列表加载态可见：`任务列表加载中...`
- 已验证空状态可见：`暂无任务，可先提交一个业务请求。`
- 已验证任务详情抽屉加载态现在可见：`任务详情加载中...`
- 已验证 AI 配置抽屉可正常拉取默认项，存在 `Default General Profile`

### 3. 访客无凭证访问受保护路由时的重定向行为
- 无注入 Hub 会话访问前端页面时，会先展示失效横幅，再自动跳转到配置的登录地址。
- 浏览器自动化验证结果：
  - `bannerContainsExpired = true`
  - `redirectTriggered = true`
  - `finalUrl = http://127.0.0.1:8999/login`
- 无凭证访问后端任务接口仍返回：
  - HTTP `401`
  - 错误码 `AUTH_REQUIRED`

### 4. `/healthz` 状态与协议
- 复验结果：HTTP `200`
- 总体状态：`degraded`
- 响应耗时：约 `12.9ms`
- `checks` 包含：
  - `database`
  - `queue`
  - `hub_registration`
  - `provider_adapter`
- `metrics` 包含：
  - `queued_jobs`
  - `running_jobs`
  - `failed_jobs_10m`
- 当前 `degraded` 原因符合预期：本地未配置 `HUB_API_URL / HUB_SERVICE_KEY`，因此 `hub_registration=degraded`，其余检查项正常。

## 结论
- 状态：`DONE_WITH_CONCERNS`
- 结论：你要求的 4 个重点项均已完成验证，且本轮暴露的 3 个真实联调问题已修复并复验通过。
- 剩余说明：Hub 真正注册/心跳成功链路未在本轮验证，因为本地环境没有配置真实 Hub 地址与服务密钥；当前只验证了“未配置时 `/healthz` 正确降级而非误报实例死亡”。
