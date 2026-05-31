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

## 部署指令

```bash
mkdir -p sub2api
cd sub2api
curl -sSL https://raw.githubusercontent.com/cclilshy/sub2api/refs/heads/override/main/override/deploy/docker-deploy.sh | bash
docker compose up -d
```
