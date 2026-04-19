import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .common_logger import get_logger
"""
后续添加中间件
"""

origins = [
    # "http://localhost.tiangolo.com",
    # "http://localhost:5173",
    # "https://localhost.tiangolo.com",
    # "http://localhost",
    # "http://localhost:8080",
    "*"
]


def add_cors_middle(app: FastAPI):
    # 1. 处理cors
    app.add_middleware(CORSMiddleware,
                       allow_origins=origins,
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"], )

    # 2. 自定义中间件
    """
       call_next一个接收request参数的函数。
       此函数会将参数传递request给相应的路径操作。
       然后它返回response由相应路径操作生成的结果。
    """
    @app.middleware("http")
    async def visit_log(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        process_time = f"{end_time - start_time:.4f}"
        client_ip = request.client.host if request.client else "未知"
        get_logger().info(
            f"客户端ip: {client_ip} | 请求方式: {request.method} | 请求路径: {request.url.path} | 耗时: {process_time}s"
        )
        response.headers["X-Process-Time"] = process_time
        return response
