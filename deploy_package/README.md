# AGV Docker Deployment Package

## 目录说明

- `backend/`：后端运行所需源码
- `frontend/`：前端源码与前端镜像构建文件
- `docker-compose.yml`：统一编排入口
- `.env.example`：数据库账号示例

## 使用方式

1. 复制 `.env.example` 为 `.env`
2. 按需修改数据库密码
3. 执行：

```bash
docker compose up -d --build
```

## 访问入口

- 前端页面：`http://服务器IP/`
- 后端硬件 TCP 端口：`13245`
