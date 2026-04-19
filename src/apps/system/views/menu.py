# 菜单相关接口
from fastapi import APIRouter
from src.apps.system.schwmas import MenuInSchema, MenuOutSchema
from src.apps.system.models import *
from src.apps.system.views.user import access_token
from fastapi import Depends
from typing import List
from src.utils.common_response import APIResponse

router = APIRouter()


# 菜单增
@router.post('/menus', description="菜单新增")
async def add_menu(menu: MenuInSchema,
                   # user: UserInfo = Depends(get_current_user)
                   ):
    await Menus.create(**menu.dict())
    return APIResponse()


# 菜单删
@router.delete('/menus', description="删除接口，单条多条都支持")
async def delete_menu(
        ids: List[int],
        # user: UserInfo = Depends(get_current_user)
):
    res = await Menus.filter(id__in=ids).update(is_delete=True)  # 软删除，字段控制
    return APIResponse(msg='菜单删除成功')


# 菜单查所有
## 1 查询所有menu接口----不分页
@router.get("/menus", description="查询所有菜单")
async def get_menu_list():
    menus = await Menus.filter().all()
    menu_dicts = [MenuOutSchema.from_orm(menu).dict() for menu in menus]
    return APIResponse(results=menu_dicts)


# 菜单查一个
@router.get("/menus/{menu_id}", description="查询菜单详情")
async def get_menu(
        menu_id: int,
        # user: UserInfo = Depends(get_current_user)
):
    menu = await Menus.filter(id=menu_id).first()
    menu_dict = MenuOutSchema.from_orm(menu).dict()
    return APIResponse(result=menu_dict)


# 菜单修改
@router.put("/menus/{menu_id}", description="查询菜单详情")
async def update_menu(
        menu_id: int,
        menu: MenuInSchema,
        # user: UserInfo = Depends(get_current_user)
):
    await Menus.filter(id=menu_id).update(**menu.dict())
    return APIResponse()
