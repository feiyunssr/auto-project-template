# TLS Certificates

此目录存放共享环境 `nginx` 挂载使用的服务端证书文件。

默认约定文件：

- `tls.fullchain.crt`
- `tls.key`

证书来源有两种：

1. 公司内部 CA 或现有正式证书
2. 仓库自带脚本 `scripts/generate_internal_tls.sh` 生成的私有 CA 签发证书

注意：

- 私钥和实际证书文件已被 `.gitignore` 忽略，不应提交到仓库
- 客户端根证书分发文件在 `infra/tls/internal-ca/root-ca.crt`
