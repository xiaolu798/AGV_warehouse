from fastapi import APIRouter, Request, Query, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse
import requests
from pydantic import BaseModel, Field, field_validator
from src.utils.common_response import APIResponse
from src.apps.home.views.schwmas import *
import pymysql
from pymysql.cursors import DictCursor  # 在头部加上这一行
import os

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

route = APIRouter()


class Excute_Sql(BaseModel):
    sql: str
    connect_info: dict


@route.post('/info')
async def cpmpute(excute_sql: Excute_Sql):
    """传入sql语句"""
    sql = excute_sql.sql
    connect_info = excute_sql.connect_info
    host = "127.0.0.1"
    conn = pymysql.connect(
        host=host,
        user=connect_info.get("user"),
        password=connect_info.get("password"),  # 别忘了密码
        database=connect_info.get("data_base"),
        port=int(connect_info.get("port", 3306)),  # 强制转 int，防止 Dify 传字符串进来
        charset='utf8mb4',
        cursorclass=DictCursor
    )
    # 2. 获取游标（卡车）
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    # 4. 记得把路关了（释放资源）
    cursor.close()
    conn.close()
    return APIResponse(data=result)


import pandas as pd
import io

"""
# Role
你是一个高级数据分析专家，擅长从 JSON 数据中提取并聚合绘图信息。

# Input Data
这是经过清洗的 JSON 数据：
{{代码执行 2.result}}

# Task
1. **智能识别**：从数据中找出最适合作为“分类标签”的列（文本/名称）和最适合作为“数值”的列（金额/数量）。
2. **数据清洗**：剔除数值中的“元”、“%”、逗号等非数字字符，转换为纯数字。
3. **求和汇总**：如果同一个分类出现了多次，请将它们的数值进行累加求和。

# Output Specification (严格遵守)
- 第一行：仅输出汇总后的数值，用分号 `;` 分隔。
- 第二行：仅输出对应的分类名称，用分号 `;` 分隔。
- **严禁**输出任何开场白、解释、Markdown 代码块或 JSON 符号。

# 示例输出
1200;800;450
研发部;市场部;行政部
"""


# http://192.168.79.1:8000/api/v1/home/main/analyze-csv
@route.post("/analyze-csv")
async def analyze_csv(file: UploadFile = File(...)):
    try:
        print(f"--- 开始处理文件: {file.filename} ---")
        contents = await file.read()

        if not contents:
            return JSONResponse(status_code=400, content={"msg": "文件内容为空"})

        # 尝试编码解析
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding='utf-8-sig')
        except:
            df = pd.read_csv(io.BytesIO(contents), encoding='gbk')

        # 转为字典列表
        df = df.head(100).fillna("")
        data = df.to_dict(orient='records')

        # 直接返回原生 JSON，不经过 APIResponse
        return JSONResponse(
            status_code=200,
            content={
                "result": data,
                "status": "success",
                "row_count": len(data)
            }
        )

    except Exception as e:
        print(f"本地报错了: {str(e)}")
        return JSONResponse(status_code=500, content={"msg": str(e), "result": []})



