# auto-project-template

`auto-project-template` 现在以 `/home/zero/external-cortex/Zero/ai-auto` 为唯一工程基线，定位是 `AI Auto` 体系下的标准数据面子服务模板，而不是另起一套独立风格的脚手架。

## 总体目的

本模板服务于一家以 Amazon 与 TikTok 为核心渠道的跨境电商公司。公司的目标不是零散地建设几个 AI 工具，而是围绕真实业务流程，持续推动从市场调研、选品与产品开发、内容生产、Listing 优化、广告投放、达人合作、客服、评论分析到库存与运营管理等环节的自动化。

因此，`auto-project-template` 的目的不是生成一个孤立的小工具，而是为这类业务环节提供统一的数据面子服务基线：把原本依赖人工执行、重复性高、可标准化的步骤沉淀为一个可接入 AI Auto Hub、可被观测、可被治理、可持续扩展的自动化服务项目。后续基于该模板孵化的新服务，都应明确自己对应 Amazon 或 TikTok 哪一个具体业务流程、替代哪一段人工操作、哪些环节仍需人工审核，而不是脱离真实业务场景单独存在。

## 项目定位

- `ai-auto` 是控制面 / Hub，负责服务注册、状态聚合、告警和治理。
- `auto-project-template` 是数据面模板，负责承载具体 AI 业务任务、AI 配置和结果沉淀，并接入 Hub 的会话与注册协议。
- 统一的是工程骨架、视觉语言、运行方式和部署基线，不是把 Hub 的业务职责直接搬进模板。

## 网关策略

当前已确定的正式环境推荐方案是：

- 平台统一使用一个共享网关承接 `Hub + 各数据面子服务`
- 子服务本身只需要暴露自己的 frontend/backend 内部服务
- 不再把“每个子项目都单独部署一个 nginx”当成默认生产方案

这意味着：

- `auto-project-template` 在正式接入时，应优先挂到平台共享网关后面
- 仓库里的 `infra/nginx/` 和 `docker-compose.yml` 继续保留，但定位调整为：
  - 独立演示环境
  - 单项目临时部署
  - 没有共享网关时的 fallback 方案

## 当前对齐结果

本轮已经把模板改造成与 `ai-auto` 同一家族的多应用仓库：

- `apps/service-backend`：FastAPI 后端，业务接口统一收敛到 `/api/v1/*`
- `apps/service-worker`：独立 worker 进程，按数据库轮询执行 `queued` 任务
- `apps/service-frontend`：Vue 3 + Vite 前端，使用 `router + pages + api + styles` 结构
- `scripts/dev.sh`：与 `ai-auto` 同风格的统一开发启动脚本
- `db/migrations/`：数据库迁移占位基线
- `docker-compose.yml`、`infra/nginx/`：独立部署 fallback 基线，不是默认生产入口
- `.env.example`：统一环境变量入口

同时保留模板自身职责：

- 任务提交、任务列表、任务详情抽屉
- 本地 AI Profile 配置中心
- Hub 登录桥接与状态透传
- `/healthz` 和 Hub 自动注册骨架
- 面向其他内部服务的 Bearer Token 异步任务 API

## 仓库结构

```text
apps/
  service-backend/
    app/
    tests/
  service-frontend/
    src/
  service-worker/
    service_worker/
db/
  migrations/
docs/
infra/
  nginx/
scripts/
  dev.sh
  generate_internal_tls.sh
```

## 本地开发

### 1. 准备依赖

```bash
cd /home/zero/external-cortex/Zero/auto-project-template

python3 -m venv .venv
./.venv/bin/pip install -e '.[dev]' -e ./apps/service-backend -e ./apps/service-worker

cd apps/service-frontend
npm install
cd ../..
```

### 2. 初始化环境文件

```bash
cp .env.example .env
```

默认本地开发值：

- Backend: `http://192.168.1.242:11010`
- Frontend: `http://192.168.1.242:11011`
- API 前缀：`/api/v1`
- 默认数据库：`sqlite+aiosqlite:///./service.db`
- 当前 IP 基线通过 `APP_SCHEME` 与 `APP_HOST_IP` 统一控制；需要切换部署机时只改这两个变量
- 服务启动后的 Hub 心跳会自动回写当前 `SERVICE_BACKEND_SERVICE_PUBLIC_BASE_URL`，所以改完 IP 配置后执行一次 `bash scripts/dev.sh restart`，Hub 里的服务入口会自动从旧地址收敛到新地址

### 3. 启动

```bash
bash scripts/dev.sh start
```

查看状态：

```bash
bash scripts/dev.sh status
```

停止：

```bash
bash scripts/dev.sh stop
```

兼容入口仍保留：

```bash
./start.sh
```

## 认证与 Hub 对接

本地默认允许开发身份回退，不强制 Hub 会话。

如果要开启真实 Hub 登录桥接：

- 后端：`SERVICE_BACKEND_REQUIRE_HUB_AUTH=true`
- 前端：`VITE_REQUIRE_HUB_AUTH=true`
- 前端：`VITE_HUB_API_BASE_URL=http://192.168.1.242:10010/api/v1`
- 前端：`VITE_HUB_LOGIN_URL=http://192.168.1.242:10011/login`

说明：

- Hub 回跳时会把 `hub_access_token` / `hub_login_url` 放进 URL，前端会立即调用 Hub `/auth/me` 校验并消费掉这些临时参数
- 子服务后端现在兼容 `X-Hub-User-Name-B64`，避免中文用户名直接作为请求头时触发浏览器 `non ISO-8859-1 code point` 错误

如果要接入真实 Hub 注册接口：

- `SERVICE_BACKEND_HUB_API_URL`
- `SERVICE_BACKEND_HUB_SERVICE_KEY`

未配置上述 Hub 注册变量时，`/healthz` 返回 `200 degraded` 属于预期。

如果 Hub 侧已经配置了 `HUB_BACKEND_INTERNAL_BOOTSTRAP_KEY`，模板现在可以直接用：

- `SERVICE_BACKEND_HUB_API_URL`
- `SERVICE_BACKEND_HUB_SERVICE_KEY`

说明：

- `SERVICE_BACKEND_HUB_SERVICE_KEY` 应与 Hub 侧的 `HUB_BACKEND_INTERNAL_BOOTSTRAP_KEY` 保持一致
- backend 会通过 `/internal/services/register` 自动换取 `service_id + service_token`
- 换取到的 telemetry 凭证会写入 `.runtime/hub-service-credentials.json`
- backend 与独立 worker 会自动复用这份凭证，把 `heartbeat`、`job_succeeded`、`job_failed` 发到 Hub

如果要走“自动接通模式”，也就是在 Hub 里只填子服务 URL、不手工填写凭证，现在模板已经补齐了子服务侧约定：

- `GET /.well-known/ai-auto-manifest.json`
- `POST /.well-known/ai-auto-bootstrap`
- 前端开发入口 `http://192.168.1.242:11011` 会代理 `/.well-known/*` 和 `/healthz` 到 backend
- `scripts/dev.sh` 默认把 `SERVICE_BACKEND_SERVICE_PUBLIC_BASE_URL` 设为前端入口 `:11011`，便于 Hub 直接登记用户实际访问的 URL
- `scripts/dev.sh` 也会默认注入 `VITE_HUB_API_BASE_URL=http://192.168.1.242:10010/api/v1` 和 `VITE_HUB_LOGIN_URL=http://192.168.1.242:10011/login`

说明：

- Hub 自动推送的运行时凭证仍会落盘到 `.runtime/hub-service-credentials.json`
- 不需要让最终用户手工填写 `SERVICE_BACKEND_HUB_SERVICE_ID` / `SERVICE_BACKEND_HUB_SERVICE_TOKEN`
- 如果你注册到共享网关域名，网关也必须放通 `/.well-known/*` 与 `/healthz`

如果你不走内部 bootstrap，也仍可手工配置以下变量作为覆盖：

- `SERVICE_BACKEND_HUB_SERVICE_ID`
- `SERVICE_BACKEND_HUB_SERVICE_TOKEN`

如果要让其他内部服务直接调用子服务任务 API，还需要配置：

- `SERVICE_BACKEND_ENABLE_SERVICE_API=true`
- `SERVICE_BACKEND_SERVICE_API_BEARER_TOKEN=<shared-internal-token>`

说明：

- `service-api` 走独立 Bearer Token 认证，不依赖 `x-hub-user-*` 头。
- `service-api` 默认只允许访问通过同一 Bearer Token 创建的任务，不会读取前端人工创建的任务。
- 当前默认协议是“异步任务型”：创建任务后返回 `task_id`，调用方自行轮询状态与结果。

## 服务间 API 调用

用于给其他内部服务调用的接口：

- `POST /api/v1/service-api/tasks`
- `GET /api/v1/service-api/tasks/{job_id}`
- `GET /api/v1/service-api/tasks/{job_id}/result`

创建任务示例：

```bash
curl -X POST http://192.168.1.242:11010/api/v1/service-api/tasks \
  -H 'Authorization: Bearer your-service-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "scenario_key": "general",
    "title": "Generate copy by API",
    "input_payload": {
      "brief": "spring sale ad copy"
    }
  }'
```

返回示例字段：

- `id`
- `job_no`
- `status`
- `current_attempt_no`
- `retryable`
- `error_code`
- `error_message`

轮询结果示例：

```bash
curl http://192.168.1.242:11010/api/v1/service-api/tasks/<job_id>/result \
  -H 'Authorization: Bearer your-service-token'
```

结果接口会返回统一状态包：

- 处理中：`status=queued|running`，`result=null`
- 成功：`status=succeeded|review_required`，`result` 带结构化结果
- 失败：`status=failed`，`result=null`，并返回 `error_code` / `error_message`

## 部署建议

正式环境推荐拓扑：

- 共享网关统一暴露域名、TLS、路由、访问日志和安全策略
- `service-frontend`、`service-backend`、`service-worker` 作为内部服务部署
- 当前仓库不要求每个子服务都再带一个独立 nginx 出口

如果当前环境还没有共享网关，仓库仍然提供可独立部署的 fallback 基线：

- `docker-compose.yml`
- `apps/service-backend/Dockerfile`
- `apps/service-worker/Dockerfile`
- `infra/nginx/`

启动示例：

```bash
cp .env.example .env
bash scripts/generate_internal_tls.sh
docker compose up --build -d
```

如果要通过内网域名访问，应先把域名指到部署机器，例如：

```text
192.168.x.x  auto-project-template.test
```

然后访问：

- `https://auto-project-template.test`

## 验证命令

后端：

```bash
cd apps/service-backend
PYTHONPATH=. ../../.venv/bin/pytest tests/test_tasks.py
```

前端：

```bash
cd apps/service-frontend
npm run typecheck
npm run build
```

## 文档

- `docs/PRD/service_prd.md`
- `docs/architecture/service_engineering_plan.md`
- `docs/a4_development_plan.md`
- `docs/design/service_design_guidelines.md`
- `DESIGN.md`
