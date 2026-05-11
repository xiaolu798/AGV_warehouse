"""
# 1 之前使用JSONResponse 返回数据，不方便，做个封装，方便我们使用
# 2 视图函数如下使用
return APIResponse()---->{code:100,msg:成功}
return APIResponse(code=101)---->{code:101,msg:成功}
return APIResponse(msg=创建成功)---->{code:101,msg:创建成功}
return APIResponse(result={name:xx,age:19})---->{code:100,msg:成功,result:{name:xx,age:19}}
"""
from fastapi import status
from typing import Optional, Any
from fastapi.responses import ORJSONResponse


class APIResponse(ORJSONResponse):
    def __init__(self, code: int = 100, msg: Optional[str] = '成功', status_code: int = status.HTTP_200_OK,
                 **kwargs) -> None:
        self.data = {
            'code': code,
            'msg': msg
        }
        self.data.update(kwargs)
        super().__init__(content=self.data, status_code=status_code)
