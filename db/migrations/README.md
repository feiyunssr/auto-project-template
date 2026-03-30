# db/migrations

当前模板已补齐与 `ai-auto` 一致的 `db/migrations/` 目录基线。

目前默认开发模式仍由 `service-backend` 在启动时执行 `SQLAlchemy metadata.create_all()` 初始化表结构，原因是模板需要保持最小接入成本。

当某个业务服务从模板演进到正式共享环境时，应将表结构固化为显式迁移脚本，并在本目录落地：

- `001_init_<service>.sql`
- 后续增量迁移脚本

正式共享环境中，建议由数据库迁移脚本负责初始化，而不是继续依赖应用启动时建表。
