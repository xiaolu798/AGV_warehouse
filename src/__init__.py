import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from tortoise.transactions import in_transaction

from src.apps.home import home_route
from src.apps.system import system_router
from src.apps.system.models import wms_mission
from .utils.common_middle import add_cors_middle
from .utils.common_db import register_mysql
from .utils.common_exception import *
from .utils.ws_connetc import ws_manager


def register_route(app: FastAPI):
    # http:127.0.0.1:8000/api/v1/system/user/***
    # 这个是路由的前缀
    app.include_router(home_route, prefix='/api/v1/home', tags=['首页所有的路由'])
    app.include_router(system_router, prefix='/api/v1/system', tags=['系统所有路由'])


def register_middle_ware(app: FastAPI):
    add_cors_middle(app)


def register_websocket(app: FastAPI):
    @app.websocket("/ws/devices")
    async def device_status_ws(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)


async def handle_hardware_signal(reader, writer):
    """
    支持双向通信的硬件处理函数
    1. 接收硬件反馈 (Read)
    2. 向硬件发送指令 (Write)
    """
    addr = writer.get_extra_info('peername')
    print(f"\n[TCP层] 硬件已上线: {addr}")

    # 将当前连接的 writer 存入全局或 app 状态，方便业务接口主动调用
    # 例如：app.state.hardware_connections[device_code] = writer

    try:
        while True:
            try:
                # 设置超时，防止死等
                data = await asyncio.wait_for(reader.readexactly(5), timeout=300.0)
            except asyncio.TimeoutError:
                # 发送心跳包保持连接 (可选)
                writer.write(b'PING')
                await writer.drain()
                continue
            except asyncio.IncompleteReadError:
                break

            # --- 解析逻辑 ---
            h_id = data[0:4].decode('utf-8').strip()
            status_code = data[4]
            print(f"[收到反馈] 任务号: {h_id}, 状态: {status_code}")

            # --- 业务处理 ---
            # 查找执行中任务
            task = await wms_mission.get_or_none(hardware_id=h_id, status=1).prefetch_related(
                'from_location', 'to_location', 'device'
            )

            if task and status_code == 1:
                async with in_transaction():
                    # 更新数据库状态 (略过已有的库位变更逻辑)
                    task.status = 2
                    await task.save()

                # --- 回传逻辑：告知助手后端已处理完毕 ---
                # 格式示例：[4字节任务号][0xEE代表确认]
                response = data[0:4] + b'\xEE'
                writer.write(response)
                await writer.drain()
                print(f"[发送确认] 已回显确认信息给助手: {response.hex()}")

                # WebSocket 广播
                await ws_manager.broadcast({"event": "mission_completed", "data": {"h_id": h_id}})
            else:
                # 任务不存在或状态不对，回传错误码 0xFF
                writer.write(data[0:4] + b'\xFF')
                await writer.drain()

    except Exception as e:
        print(f"[TCP异常] {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"[TCP层] 硬件离线: {addr}")




def register_hardware_server(app: FastAPI):
    @app.on_event("startup")
    async def startup_hardware_server():
        server = await asyncio.start_server(handle_hardware_signal, '127.0.0.1', 13245)
        app.state.hardware_server = server
        print("工业协议监听服务已启动: 127.0.0.1:13245")

    @app.on_event("shutdown")
    async def shutdown_hardware_server():
        server = getattr(app.state, "hardware_server", None)
        if server is not None:
            server.close()
            await server.wait_closed()
            print("工业协议监听服务已关闭")


def create_app() -> FastAPI:
    # 1. 实例化得到app对象
    app = FastAPI()
    # 2.注册路由
    register_route(app)
    # 3. 注册中间件
    register_middle_ware(app)
    # 4. 注册ORM,调用这个register_mysql
    register_mysql(app)
    # 5. 注册WebSocket
    register_websocket(app)
    # 6. 注册硬件TCP监听服务
    register_hardware_server(app)

    # 统一注册异常处理器
    register_exception(app)

    # 开启media文件访问
    app.mount('/media', StaticFiles(directory='media'), name='媒体文件访问')
    return app
