from pydantic import BaseModel
from typing import *


# --- 1. 定义 Dify 要求的请求体 ---
class DifyRetrievalRequest(BaseModel):
    query: str  # Dify 传过来的原始问题
    knowledge_id: Optional[str] = None
    top_k: int = 5  # 找回多少条相关片段
