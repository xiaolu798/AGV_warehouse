# src/utils/common_exception.py

from fastapi.exceptions import RequestValidationError
from .common_response import APIResponse
from fastapi import FastAPI, Request


def register_exception(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        errors = exc.errors()
        # 提取报错信息
        msg = errors[0].get("msg")
        field = errors[0].get("loc")[-1]

        return APIResponse(code=400, msg=f"参数错误: {field} {msg}", status_code=400)

    # 你甚至可以再加一个全局未捕获异常
    @app.exception_handler(Exception)
    async def all_exception_handler(request, exc):
        return APIResponse(code=500, msg="服务器开小差了", status_code=500)
