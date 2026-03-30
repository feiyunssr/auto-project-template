# infra/nginx

共享环境正式基线的 Nginx 入口放在这里。

当前目录包含：

- `Dockerfile`：构建共享环境网关镜像，并在构建阶段打包前端静态文件
- `nginx.conf`：Nginx 主配置
- `templates/default.conf.template`：共享环境 HTTPS 网关模板
- `certs/`：Nginx 挂载的服务端证书目录

当前阶段职责：

- 作为共享环境统一入口，对外暴露 `80/443`
- 提供前端静态资源
- 反向代理 `/api/`、`/docs`、`/openapi.json` 到 `service-backend`
- 在 `80` 上做 HTTP 到 HTTPS 跳转
- 在 `443` 上终止 TLS

证书接入方式：

- 优先直接挂载公司内部 CA 或正式签发的证书
- 如果当前没有企业 CA，可使用 `scripts/generate_internal_tls.sh` 生成私有根 CA 和服务端证书
