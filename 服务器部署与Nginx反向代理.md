# AGV 项目上传与部署流程

## 1. 当前部署方案说明

本文档基于当前项目最新整理后的发布目录：

- 发布目录为 `deploy_package`
- 后端入口为 `main.py`
- 后端核心代码在 `src/`
- 前端目录已经整理到 `deploy_package/frontend`
- 使用 `docker compose` 统一启动：
  - `mysql`
  - `backend`
  - `frontend`
- 前端容器内置 `nginx`
- 前端 API 基地址默认是 `/api/v1/system`
- 前端 WebSocket 默认地址是 `/ws/devices`

当前项目里这两个路径已经确认无误：

- HTTP 接口前缀：`/api/v1/system`
- WebSocket 路径：`/ws/devices`

对应关系如下：

- 浏览器访问首页时，进入前端 Nginx
- 前端静态资源由 Nginx 返回
- Nginx 把 `/api/` 转发到后端 FastAPI
- Nginx 把 `/ws/` 转发到后端 WebSocket

## 2. 发布目录结构

本次建议上传的目录不是整个仓库，而是已经整理好的：

```text
deploy_package/
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── src/
│   ├── migrations/
│   └── media/
├── frontend/
│   ├── Dockerfile
│   ├── default.conf
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   └── src/
├── .env.example
├── docker-compose.yml
└── README.md
```

说明：

- `backend/` 只保留真正运行需要的后端代码
- `frontend/` 保留前端源码，由 Docker 在虚拟机里构建
- `.env.example` 是数据库配置示例
- `docker-compose.yml` 是统一部署入口

## 3. 本地打包上传

### 第一步：确认前端源码已经修好

因为当前方案是把前端源码一起上传到虚拟机，再由 Docker 构建，所以在本地不一定要先打 `dist`。

建议至少确认：

- `frontend/package.json` 正常
- 前端页面能正常构建
- 前端 API 路径仍然是 `/api/v1/system`
- 前端 WebSocket 路径仍然是 `/ws/devices`

### 第二步：在 Windows 本地打包

在项目根目录执行：

```bash
cd /d f:\KongOA_Backend
tar -cvf deploy_package.tar deploy_package
```

如果你想压缩得更小，也可以：

```bash
cd /d f:\KongOA_Backend
tar -czvf deploy_package.tar.gz deploy_package
```

## 4. 上传到 Ubuntu 虚拟机

### 方案 A：使用 `scp`

在 Windows 本地执行：

```bash
scp deploy_package.tar sc@你的服务器IP:~/
```

如果你传的是压缩版：

```bash
scp deploy_package.tar.gz sc@你的服务器IP:~/
```

### 方案 B：用 WinSCP 或其他图形工具

也可以直接把 `deploy_package.tar` 或 `deploy_package.tar.gz` 上传到虚拟机用户家目录：

```text
/home/sc
```

## 5. 在虚拟机上解压

登录虚拟机：

```bash
ssh sc@你的服务器IP
```

创建部署目录：

```bash
sudo mkdir -p /opt/agv
sudo chown -R sc:sc /opt/agv
cd /opt/agv
```

如果你上传的是 `tar`：

```bash
tar -xvf ~/deploy_package.tar
```

如果你上传的是 `tar.gz`：

```bash
tar -xzvf ~/deploy_package.tar.gz
```

最终目录应为：

```text
/opt/agv/deploy_package
```

## 6. 安装 Docker 与 Docker Compose

如果虚拟机还没有安装 Docker，执行：

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

验证：

```bash
docker --version
docker compose version
```

如果当前用户没有 Docker 权限，可以临时用 `sudo docker`，或者把用户加入 Docker 组：

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 7. 配置环境变量

进入部署目录：

```bash
cd /opt/agv/deploy_package
```

复制配置模板：

```bash
cp .env.example .env
```

按需修改数据库账号密码：

```bash
vim .env
```

示例内容：

```env
MYSQL_ROOT_PASSWORD=PleaseChangeThisRootPassword
MYSQL_DATABASE=oa_backend
MYSQL_USER=agv
MYSQL_PASSWORD=agv123456
```

## 8. 使用 Docker Compose 启动

在部署目录执行：

```bash
cd /opt/agv/deploy_package
docker compose up -d --build
```

说明：

- `mysql` 容器负责数据库
- `backend` 容器负责 FastAPI
- `frontend` 容器内置 Nginx，负责：
  - 前端静态页面
  - `/api/` 反向代理
  - `/ws/` WebSocket 反向代理

## 9. 当前反向代理规则

当前前端实际访问路径如下：

- API 基地址：`/api/v1/system`
- WebSocket 地址：`/ws/devices`

当前 Nginx 配置对应逻辑为：

```nginx
location /api/ {
    proxy_pass http://backend:8080;
}

location /ws/ {
    proxy_pass http://backend:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

这里是正确的，原因是：

- 前端访问 `/api/v1/system/user/login`
- Nginx 不改写路径，直接转发给 `backend:8080`
- 后端本身注册的就是 `/api/v1/system/...`

WebSocket 也是一样：

- 前端访问 `/ws/devices`
- Nginx 直接转发 `/ws/devices`
- 后端已注册 `/ws/devices`

## 10. 查看容器状态

查看运行状态：

```bash
docker compose ps
```

查看全部日志：

```bash
docker compose logs -f
```

查看后端日志：

```bash
docker compose logs -f backend
```

查看前端日志：

```bash
docker compose logs -f frontend
```

查看数据库日志：

```bash
docker compose logs -f mysql
```

## 11. 部署成功后如何验证

### 1. 验证首页

浏览器访问：

```text
http://你的服务器IP/
```

如果页面打开正常，说明前端容器和 Nginx 已正常工作。

### 2. 验证接口

在虚拟机上执行：

```bash
curl http://127.0.0.1/api/v1/system/warehouse
```

如果没有安装本机 Nginx，也可以直接从容器端口验证：

```bash
curl http://127.0.0.1:80/api/v1/system/warehouse
```

或者从浏览器直接访问：

```text
http://你的服务器IP/api/v1/system/warehouse
```

### 3. 验证 WebSocket

前端打开页面后，检查浏览器控制台：

- 是否出现 `/ws/devices` 连接成功
- 是否没有 `WebSocket closed` 或 `404`

## 12. Cloudflare Tunnel 配合方式

你当前虚拟机里已经运行了 `cloudflared` 容器，并且日志显示已经成功建立连接：

- `Registered tunnel connection` 已出现多次

这说明隧道主连接已经起来了。

### 建议的映射方式

因为你的前端容器对外暴露的是 `80` 端口，所以 Cloudflare Tunnel 的目标服务建议直接指向：

```text
http://127.0.0.1:80
```

也可以写成：

```text
http://localhost:80
```

这样访问 Cloudflare 分配的域名时：

- `/` 会到前端页面
- `/api/...` 会由前端 Nginx 转发给后端
- `/ws/...` 会由前端 Nginx 升级并转发给后端

### 如果你在 Cloudflare 后台配置 Public Hostname

建议：

- Hostname：你的域名或子域名
- Service Type：`HTTP`
- URL：`http://127.0.0.1:80`

不要把 Cloudflare 直接指向后端 `8080`，否则：

- 前端静态页面不会走同一个入口
- `/ws/` 与 `/api/` 的统一代理也会变复杂

## 13. 你当前 Cloudflare Tunnel 命令的注意点

你现在的命令核心思路是对的，但这里有一个细节要注意：

你写的是：

```bash
-e http_proxy= `http://192.168.31.251:7890`
-e https_proxy= `http://192.168.31.251:7890`
```

这里的反引号不建议使用，因为 Bash 会把反引号当成命令替换。

更稳妥的写法是：

```bash
sudo docker rm -f cloudflare-tunnel

sudo docker run -d --name cloudflare-tunnel \
  --dns 8.8.8.8 --dns 1.1.1.1 \
  -e http_proxy=http://192.168.31.251:7890 \
  -e https_proxy=http://192.168.31.251:7890 \
  --restart always \
  cloudflare/cloudflared:latest tunnel --no-autoupdate run \
  --token 你的token \
  --protocol http2
```

## 14. 关于日志里的 DNS 超时

你提供的日志里有：

```text
ERR Failed to initialize DNS local resolver error="lookup region1.v2.argotunnel.com: i/o timeout"
ERR Failed to refresh DNS local resolver error="lookup region1.v2.argotunnel.com: i/o timeout"
```

但同时也有：

```text
Registered tunnel connection
```

这说明：

- Tunnel 主连接已经建立成功
- 但容器内部本地 DNS 刷新存在超时问题

目前这不一定会立即影响访问，但建议后续排查：

- 宿主机 DNS 是否稳定
- 代理是否对 DNS 请求有限制
- Docker 默认网络 DNS 是否存在间歇性超时

如果后面 Cloudflare 域名偶发打不开，就重点查这里。

## 15. 常见问题排查

### 问题 1：前端页面能打开，但接口 404

检查：

- 前端请求前缀是否还是 `/api/v1/system`
- 前端 Nginx 是否正确代理 `/api/`
- 后端容器是否正常启动

验证：

```bash
docker compose logs -f backend
curl http://127.0.0.1:80/api/v1/system/warehouse
```

### 问题 2：WebSocket 连接失败

检查：

- 前端 WebSocket 地址是否还是 `/ws/devices`
- Nginx 是否配置了：
  - `proxy_http_version 1.1`
  - `Upgrade`
  - `Connection "upgrade"`
- 后端是否注册了 `/ws/devices`

### 问题 3：前端构建失败

检查：

- `frontend/package.json` 是否完整
- 前端依赖是否写全
- Vue / Vite 配置是否正确

查看前端构建日志：

```bash
docker compose build frontend --no-cache
```

### 问题 4：数据库初始化失败

检查：

- `.env` 里的数据库账号密码是否正确
- `mysql` 容器是否健康
- `backend` 是否在等待 MySQL 完成启动

查看：

```bash
docker compose ps
docker compose logs -f mysql
docker compose logs -f backend
```

### 问题 5：Cloudflare 域名可以打开，但资源异常

检查：

- Public Hostname 是否指向了 `http://127.0.0.1:80`
- 是否错误地直接指到了后端 `8080`
- Cloudflare 是否开启了正确的 WebSocket 支持

## 16. 最终上线命令汇总

### 本地打包

```bash
cd /d f:\KongOA_Backend
tar -czvf deploy_package.tar.gz deploy_package
```

### 上传

```bash
scp deploy_package.tar.gz sc@你的服务器IP:~/
```

### 虚拟机解压

```bash
sudo mkdir -p /opt/agv
sudo chown -R sc:sc /opt/agv
cd /opt/agv
tar -xzvf ~/deploy_package.tar.gz
```

### 启动

```bash
cd /opt/agv/deploy_package
cp .env.example .env
docker compose up -d --build
```

### 查看日志

```bash
docker compose logs -f
```

### 验证接口

```bash
curl http://127.0.0.1:80/api/v1/system/warehouse
```

## 17. 一句话描述这套方案

你可以这样描述：

- 前端和后端代码先整理成 `deploy_package`
- 通过 `tar` 上传到 Ubuntu 虚拟机
- 使用 `docker compose` 一次启动 MySQL、FastAPI、Nginx 前端容器
- 前端通过 Nginx 统一暴露入口
- `/api/` 代理到 FastAPI
- `/ws/` 代理到 WebSocket
- 最后再通过 Cloudflare Tunnel 把 `80` 端口映射到公网访问
