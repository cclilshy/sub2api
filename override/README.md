# Sub2API Override Deployment

专用部署入口

```text
cclilshy/sub2api:latest
```

## 发布镜像

在本地源码仓库根目录执行

```bash
git checkout override/main

VERSION="$(tr -d '\r\n' < backend/cmd/server/VERSION)"
COMMIT="$(git rev-parse --short HEAD)"
DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg VERSION="$VERSION" \
  --build-arg COMMIT="$COMMIT" \
  --build-arg DATE="$DATE" \
  -t cclilshy/sub2api:latest \
  --push \
  .
```

## 更新部署脚本

```bash
python3 override/update.py
```

## 一次性调整用户 ID 自增数

生产环境部署目录中执行（例如 `sub2api/`，包含 `docker-compose.local.yml` 的目录）：

```bash
curl -sSL https://raw.githubusercontent.com/cclilshy/sub2api/refs/heads/override/main/override/deploy/adjust-user-id-sequence.sh \
  | bash -s -- --next 10000 --dry-run

curl -sSL https://raw.githubusercontent.com/cclilshy/sub2api/refs/heads/override/main/override/deploy/adjust-user-id-sequence.sh \
  | bash -s -- --next 10000
```

脚本会通过 Docker Compose 进入 PostgreSQL 容器，锁定 `users` 表，并把真正的下一个自增 ID 调整为 `max(MAX(users.id)+1, --next)`，避免指定值小于现有最大 ID 时产生冲突。

## 部署指令

```bash
mkdir -p sub2api
cd sub2api
curl -sSL https://raw.githubusercontent.com/cclilshy/sub2api/refs/heads/override/main/override/deploy/docker-deploy.sh | bash
docker compose up -d
```
