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

- Backend: `http://127.0.0.1:11010`
- Frontend: `http://127.0.0.1:11011`
- API 前缀：`/api/v1`
- 默认数据库：`sqlite+aiosqlite:///./service.db`

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

如果你不走内部 bootstrap，也仍可手工配置以下变量作为覆盖：

- `SERVICE_BACKEND_HUB_SERVICE_ID`
- `SERVICE_BACKEND_HUB_SERVICE_TOKEN`

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
