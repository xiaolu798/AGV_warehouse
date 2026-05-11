from fastapi import APIRouter, HTTPException, status, Query
from src.apps.system.schwmas import LoginRequest, UserSchemas
from src.apps.system.models import *
from src.utils.common_response import APIResponse
from src.settings import setting
from datetime import timedelta, datetime
from jose import jwt, JWTError
from pydantic import BaseModel

router = APIRouter()


# 根据用户名生成token
def create_access_token(data: dict, expire_delta: timedelta = None):
    """
    expire_delta: 默认过期时间为30分钟
    :return:
    """
    to_encode = data.copy()
    # 过期时间传了,也就是
    if expire_delta:
        # 当前时间 + 过期时间，只要不大于过期时间，token合法
        expire = datetime.utcnow() + expire_delta
    else:
        # 如果没有传，用配置文件
        expire = timedelta(minutes=setting.ACCESS_TOKEN_expire_time) + datetime.utcnow()
    # 更新data的值
    to_encode.update({'exp': expire})
    #
    encode_jwt = jwt.encode(to_encode, setting.SERCERT_KEY, algorithm=setting.ALGORITHMS)
    return encode_jwt


async def authenticate_user(username: str, password: str):
    user = await User.get_or_none(username=username)
    if user:
        # 2. 调用实例方法。传入前端传来的明文 password
        # 它会返回 True 或 False
        # 用user实例对象来调用这个check_password
        if user.check_password(password):
            return user
    return None


@router.post('/login')
async def login(login_request: LoginRequest):
    # 1. FastAPI 看到 LoginRequest，自动去 Body 里找数据
    # 2. 自动把 JSON 转成 LoginRequest 的对象实例
    # 3. 你可以直接用点语法取值

    # 根据这个前端传过来的数据进行效验
    user: User = await authenticate_user(login_request.username, login_request.password)
    if not user:
        return APIResponse(code=400, msg="用户名或密码错误")
    # 通过用户名，签发token
    token = create_access_token(data={'username': user.username},  # <--- 【A点】在这里定义的 key,解码是可以取出查看对应的用户
                                expire_delta=timedelta(minutes=setting.ACCESS_TOKEN_expire_time))
    # 返回给前端
    """
    // 前端 console.log(res.data) 的结果：
    {    
        "code": 100,
        "msg": "成功",
        "username": "admin",
        "avatar": "default.png",
        "token": "eyJhbGciOiJIUzI1Ni..."
    }
    """
    return APIResponse(username=user.username, avatar=user.avatar, token=token)


"""认证：依赖注入 所有需要登录才能访问的接口 """
from fastapi.security import OAuth2PasswordBearer  # 要求前端请求头中 authentication:Bearer token三段式
from fastapi import Depends, Request  # 在执行某个请求是，先执行这个依赖注入的函数方法

"""
当你把 oauth2 注入到接口中时，它会自动执行以下逻辑：

自动寻找 Header：它会检查每个进入服务器的 HTTP 请求头。

锁定关键词：它只寻找 Authorization 字段。

解析格式：它要求值必须是 Bearer <Token>。

提取结果：它会把 Bearer  后面的那串长长的 JWT 字符串提取出来，赋值给你函数里的变量。
"""
oauth2 = OAuth2PasswordBearer(tokenUrl='token')


async def oauth2_scheme(request: Request):
    try:
        token = await oauth2(request)
        return token
    except Exception as e:
        # 补全异常：当找不到 Token 或格式不对时触发
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证，请重新登录",
            # 标准做法：增加这个 Header，告诉浏览器或前端需要 Bearer 认证
            headers={"WWW-Authenticate": "Bearer"},
        )


async def access_token(token: str = Depends(oauth2_scheme)):
    try:
        # 2. 解码你在 login 里生成的 token
        pyload = jwt.decode(token, setting.SERCERT_KEY, algorithms=[setting.ALGORITHMS])
        username = pyload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="无效 Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 已失效")
    user = await User.get_or_none(username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="当前用户不存在")
    return user


"""查询单个用户"""


@router.get('/users/{user_id}', description='查询单个用户')
async def get_user(user_id: int,
                   user: User = Depends(access_token)
                   ):
    # 查询单个用户
    user_serializer = await User.filter(id=user_id).first()
    if not user_serializer:
        return APIResponse(code=404, msg="该用户不存在", result=None)
    user_detail = UserSchemas.model_validate(user_serializer).model_dump()
    return APIResponse(result=user_detail)


"""查询所有的用户，并分页展示"""
from typing import Optional


# Query指定传入数据的格式和限制

# 分页的参数
class PaginationParams(BaseModel):
    page: int = Query(default=1, description='当前页码')
    page_size: int = Query(5, ge=1, le=100, description="每页数据条数,1~100")


"""q: Optional[str] = None): # q 可以是字符串，也可以是 None"""


class UserParams(BaseModel):
    username: Optional[str] = Query(None, description='用户名')
    nickname: Optional[str] = Query(None, description="姓名中文名")
    is_active: bool = Query(True, description='状态')

    def to_quesry_params(self):
        query_params = {}
        """将类中的成员变成字典，包括page，page_size"""
        for item, value in self.__dict__.items():
            if value is not None:
                if item in ["username", "nickname"]:
                    query_params[f"{item}__icontains"] = value
                else:
                    query_params[item] = value
        return query_params


"""http://localhost:8000/user?page=1&size=10&username=zx&is_active=true"""


@router.get('/users', description='查询所有的用户')
async def get_userInfo(
        user_query: UserParams = Depends(),
        page_query: PaginationParams = Depends(),
        # user: User = Depends(access_token)
):
    # Depends()可以自动将url参数匹配username,nickname,is_active
    search = user_query.to_quesry_params()  # username__icontains

    offset = (page_query.page - 1) * page_query.page_size
    # 总共多少数据,每一页展示10条数据，可以查看分多少页
    total = await User.filter(**search, is_delete=False).count()
    # 3. 使用你的 APIResponse返回,使用prefetch_related关联字段roles去另一个表查询
    users = await User.filter(**search, is_delete=False).all().prefetch_related('roles').offset(offset).limit(
        page_query.page_size)  # **search自动piper传入

    # 的参数

    # 序列化
    # model_validate 把对象转成 Pydantic 实例，model_dump 把实例转成字典
    user_list = [UserSchemas.model_validate(user).model_dump() for user in users]
    return APIResponse(
        result=user_list,
        total=total,
        page=page_query.page,
        size=page_query.page_size
    )


"""删除一条或多条用户信息"""


@router.delete('/users/', description='删除单个用户或删除多个')
async def delete_user(user_ids: list[int]):
    res = await User.filter(id__in=user_ids).update(is_delete=True)  # 软删除，没有彻底删除
    if res:
        return APIResponse(msg='删除成功')
    else:
        return APIResponse(msg='删除成功')
