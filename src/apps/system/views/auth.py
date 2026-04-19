from src.utils.common_response import APIResponse
from fastapi import APIRouter, Depends
from src.apps.system.models import User
from src.apps.system.views.user import *

router = APIRouter()
"""不同拥护登录后看到的界面不同，权限管理"""


@router.get('/auths')
async def menu(user: User = Depends(access_token)):
    # 这里能拿到是哪个用户----》去数据库查出该用户的菜单权限
    # 把菜单权限处理成前端需要的样子--》返回给前端
    nav = [
        {
            'name': 'SysManga',
            'title': '系统管理',
            'icon': 'Setting',  # 🔧 换成了 Setting (设置齿轮)
            'component': '',
            'path': '',
            'children': [
                {
                    'name': 'SysUser',
                    'title': '用户管理',
                    'icon': 'UserFilled',  # 👤 换成了 UserFilled (用户)
                    'path': '/admin/user',
                    'component': 'admin/User',
                    'children': []
                },
                {
                    'name': 'SysRole',
                    'title': '角色管理',
                    'icon': 'Briefcase',  # 💼 换成了 Briefcase (角色/职务)
                    'path': '/admin/role',
                    'component': 'admin/Role',
                    'children': []
                },
                {
                    'name': 'SysMenu',
                    'title': '菜单管理',
                    'icon': 'Menu',  # 📜 换成了 Menu (菜单列表)
                    'path': '/admin/menu',
                    'component': 'admin/Menu',
                    'children': []
                },
                {
                    'name': 'SysDept',
                    'title': '部门管理',
                    'icon': 'Avatar',  # 🏢 换成了 Avatar (组织架构/人像)
                    'path': '/admin/dept',
                    'component': 'admin/Dept',
                    'children': []
                },
                {
                    'name': 'SysJob',
                    'title': '岗位管理',
                    'icon': 'Suitcase',  # 💼 换成了 Suitcase (岗位)
                    'path': '/admin/job',
                    'component': 'admin/Job',
                    'children': []
                }
            ]
        },
        {
            'name': 'SysTools',
            'title': '系统工具',
            'icon': 'Tools',  # 🛠️ 换成了 Tools (工具箱)
            'path': '',
            'component': '',
            'children': [
                {
                    'name': 'SysDict',
                    'title': '数字字典',
                    'icon': 'Notebook',  # 📖 换成了 Notebook (字典/账本)
                    'path': '/admin/dicts',
                    'component': 'admin/Dicts',
                    'children': []
                },
            ]
        }
    ]
    # 按钮权限
    # 下面表示当前用户有 ：sys系统管理，user用户页面：查看所有，新增，删除
    authoritys = ['sys:user:list', "sys:user:save", "sys:user:delete"]

    return APIResponse(nav=nav, authoritys=authoritys)
