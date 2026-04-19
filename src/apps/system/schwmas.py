"""
使用-pydantic
"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from typing import List, Any, Optional

from src.apps.system.models import Dept


class LoginRequest(BaseModel):
    username: str
    password: str


"""定义返回给前端的字段"""


class RoleSchemas(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True  # 👈 注意：这里要设为 True
    }


class UserSchemas(BaseModel):
    id: int = Field(description='用户ID')
    username: str
    avatar: str
    email: str
    phone: str
    gender: str
    is_active: bool
    nick_name: str
    roles: List[RoleSchemas]

    # 序列化一下头像url，v指的是要序列化字段
    @field_validator('avatar')
    @classmethod
    def format_avatar_url(cls, v: str):
        if v:
            v = f"http://127.0.0.1:8080/media/{v}"
            return v
        return v

    """里面可以写效验字段"""
    # 核心配置：允许从类属性中提取数据，将数据库查询到的数据对象转换成字典
    model_config = {
        "from_attributes": True  # 👈 注意：这里要设为 True
    }


# class DeptSchemas(BaseModel):
#     id: int
#     name: str
#     enabled: bool
#     sub_count: int
#     dept_sort: int
#     pid_id: Optional[int]
#     # 根据pid查出是一个父对象，根据pid_id查出的是当前服部门的id
#     children: List["DeptSchemas"] = []
#
#     # 核心配置：允许从类属性中提取数据，将数据库查询到的数据对象转换成字典
#     model_config = {
#         "from_attributes": True
#     }
#     # @classmethod
#     # async def from_orm_recurse(cls, obj: Any):
#     #     # 这个obj是一个部门对象,cls.from_orm就是使用这个DeptSchemas序列化
#     #     dept_dict = cls.model_validate(obj).model_dump(exclude={'children'})
#     #     # 把children查出来,这是一个列表
#     #     children = obj.children.all()
#     #     # 3. 递归处理子部门，并手动塞进字典,children是一个子部门对象
#     #     dept_dict["children"] = [await cls.from_orm_recurse(child) for child in children]
#     #     return dept_dict
class DeptSchemas(BaseModel):
    id: int
    name: str
    enabled: bool
    dept_sort: Optional[int] = 0
    pid_id: Optional[int] = None
    children: List["DeptSchemas"] = []

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def build_tree(cls, all_depts) -> List[dict]:
        """
        方案 B：手动构造字典映射，彻底避开 Pydantic 校验报错
        """
        # 1. 第一步：手动将 ORM 对象转换为干净的字典，查出所有的部门
        dept_map = {}
        for d in all_depts:
            dept_map[d.id] = {
                "id": d.id,
                "name": d.name,
                "enabled": d.enabled,
                "dept_sort": d.dept_sort or 0,
                "pid_id": d.pid_id,  # 这里的 pid_id 是数据库物理字段
                "children": []  # 初始化自己的子部门列表
            }

        # 2. 第二步：建立层级关系
        tree = []
        for d in all_depts:
            node = dept_map[d.id]
            parent_id = node.get("pid_id")

            if parent_id is None:
                # 根部门，直接放入结果树
                tree.append(node)
            else:
                # 子部门，去找它的爸爸
                parent_node = dept_map.get(parent_id)
                if parent_node is not None:
                    # 关键：由于是字典引用，这里的修改会同步到 tree 里的层级
                    parent_node["children"].append(node)

        return tree


# 新增一个部门时，肯定没有一个子部门
######## 序列化类
class DeptInSchema(BaseModel):
    pid_id: int | None = None
    name: str
    enabled: bool
    sub_count: int | None = None
    dept_sort: int

    class Config:
        from_attributes = True


class JobSchemas(BaseModel):
    id: int
    name: str
    enabled: bool
    job_sort: int

    # 核心配置：允许从类属性中提取数据，将数据库查询到的数据对象转换成字典
    model_config = {
        "from_attributes": True  # 👈 注意：这里要设为 True
    }


# 菜单相关
class MenuInSchema(BaseModel):
    pid_id: int | None = None
    sub_count: int | None = None
    # 0 菜单，1 子菜单，2 按钮
    type: int
    title: str
    name: str
    component: str | None = None
    menu_sort: int
    icon: str
    path: str
    i_frame: bool
    cache: bool
    hidden: bool
    permission: str | None = None
    is_menu: bool

    class Config:
        from_attributes = True


class MenuOutSchema(BaseModel):
    id: int
    sub_count: int | None = None
    # 0 菜单，1 子菜单，2 按钮
    type: int
    title: str
    name: str
    component: str | None = None
    menu_sort: int
    icon: str
    path: str
    i_frame: bool
    cache: bool
    hidden: bool
    permission: str | None = None
    is_menu: bool

    class Config:
        from_attributes = True


class RoleOutSchema(BaseModel):
    id: int
    name: str
    level: int
    description: str
    data_scope: str
    status: bool

    # 关联关系：db_table 指定中间表的名字
    # depts : list[DeptOutSchema]
    # menus : list[MenuOutSchema]

    class Config:
        from_attributes = True


class RoleInSchema(BaseModel):
    name: str
    level: int
    description: str
    data_scope: str
    status: bool

    # 关联关系：db_table 指定中间表的名字
    # depts : list[DeptOutSchema]
    # menus : list[MenuOutSchema]

    class Config:
        from_attributes = True


class MissionCreateSchema(BaseModel):
    type: int
    priority: int | None = None
    from_location: str
    to_location: str
    device_code: Optional[str] = None

    class Config:
        from_attributes = True  # 允许从 ORM 对象转换


# 1. 创建仓库时用的（前端传给后端）
class WarehouseCreateSchema(BaseModel):
    name: str = Field(..., description="仓库名称", example="原材料仓")
    code: str = Field(..., description="仓库编码", example="WH-A")
    rows: int = Field(default=10, ge=1, description="矩阵行数")
    cols: int = Field(default=10, ge=1, description="矩阵列数")
    description: Optional[str] = None


# 2. 修改仓库时用的（可选更新字段）
class WarehouseUpdateSchema(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    # 注意：通常不允许直接修改 rows/cols，因为会破坏已有的库位布局


# 3. 返回给前端展示用的（包含 ID 和状态）
# 修改 WMSWarehouseSchema 增加几个可选字段
class WMSWarehouseSchema(BaseModel):
    id: int
    name: str
    code: str
    rows: int
    cols: int
    is_active: bool
    # 增加统计字段
    total_slots: Optional[int] = 0
    used_slots: Optional[int] = 0

    class Config:
        from_attributes = True


class WMSLocationSchema(BaseModel):
    id: int
    location_code: str
    status: int
    row_index: int
    col_index: int
    # 增加仓库信息展示
    warehouse: Optional[WMSWarehouseSchema] = None

    class Config:
        from_attributes = True


class DeviceSchema(BaseModel):
    id: int
    device_code: str
    device_type: int
    is_active: bool
    work_status: int
    battery: int

    class Config:
        from_attributes = True  # 允许从 Tortoise 对象直接转换


# --- 2. 展示列表时用的 Schema (后端返给前端) ---
class MissionOutSchema(BaseModel):
    id: int
    mission_no: str
    type: int
    status: int
    priority: Optional[int] = None
    hardware_id: str

    # 核心：这里会嵌套返回库位的详细信息（包含坐标和编号）
    from_location: Optional[WMSLocationSchema] = None
    to_location: Optional[WMSLocationSchema] = None

    # 如果有设备关联，也可以带上设备信息
    device: Optional[DeviceSchema] = None

    create_time: datetime

    class Config:
        from_attributes = True
