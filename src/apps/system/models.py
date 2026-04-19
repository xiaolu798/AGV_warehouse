from tortoise import models, fields
from passlib.context import CryptContext
from src.utils.common_model import *

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class User(BaseModel):
    username = fields.CharField(max_length=255, description='用户名')
    password = fields.CharField(max_length=128, description='用户密码')
    avatar = fields.CharField(max_length=255, default='avatar/default.png', description='头像')
    is_active = fields.BooleanField(default=True, description='是否为活跃用户')
    email = fields.CharField(max_length=32, description='邮箱', null=True)
    nick_name = fields.CharField(max_length=32, description='用户昵称', null=True, unique=True)
    gender = fields.CharField(max_length=16, description='性别', null=True)
    phone = fields.CharField(max_length=11, description='电话号码', null=True, unique=True)
    enabled = fields.BooleanField(default=True, description='是否弃用？状态:1启用、0禁用')
    is_superuser = fields.BooleanField(default=False, description='是否为超级用户')

    # 用户跟角色，多对多
    roles = fields.ManyToManyField(model_name='models.Role', description='用户和角色的关联表', through='oa_users_role')

    # 用户跟部门 一对多
    dept = fields.ForeignKeyField(model_name='models.Dept', on_delete=fields.SET_NULL, description='部门名字', null=True)

    # 用户跟岗位
    job = fields.ManyToManyField(model_name='models.Job', description='岗位名称', through='oa_users_job')

    class Meta:
        table = "oa_users"

    def __str__(self):
        return self.username

    # 类上写一个方法--> 通过明文得到密文的方法,类的方法，创建用户的时候，还没有对象，只有类
    @classmethod
    def make_password(cls, password: str):
        return pwd_context.hash(password)

    # self.password为密文
    def check_password(self, password: str):
        # 到时候直接调用这个方法
        return pwd_context.verify(password, self.password)


class OnlineUser(BaseModel):
    brower = fields.CharField(max_length=255, description='用户登录浏览器')
    ip = fields.CharField(max_length=64, description='用户登录IP', null=True)
    key = fields.CharField(max_length=255, description='用户token', null=True)
    user = fields.ForeignKeyField(model_name='models.User', null=True)  # 指向用户表

    class Meta:
        table = "online_user"


# 菜单，权限展示不同菜单按钮
"""

关联自己的外键一般用于处理树形结构
| id | name | pid | 说明 |
| :--- | :--- | :--- | :--- |
| 1 | 系统管理 | NULL | 顶级菜单 |
| 2 | 用户管理 | 1 | “系统管理”的子菜单 |
| 3 | 角色管理 | 1 | “系统管理”的子菜单 |
| 4 | 权限设置 | 3 | “角色管理”的子菜单 |
"""


class Menus(BaseModel):
    pid = fields.ForeignKeyField(model_name='models.Menus', description='父菜单id', on_delete=fields.SET_NULL, null=True)
    sub_count = fields.IntField(description='子菜单数目', null=True, blank=True)
    # 0.菜单 1.子菜单 2 按钮
    type = fields.IntField(description='菜单类型', null=True)
    title = fields.CharField(max_length=32, description='菜单标题', null=True, unique=True)
    name = fields.CharField(max_length=255, description='前端组件名称', null=True, unique=True)
    component = fields.CharField(max_length=255, description='前端组件', null=True)
    menu_sort = fields.IntField(description='菜单排序', null=True)
    icon = fields.CharField(max_length=255, null=True, description='菜单图标')
    path = fields.CharField(max_length=255, null=True, description='菜单连接地址')
    i_frame = fields.BooleanField(default=False, description='是否外链')
    cache = fields.BooleanField(default=False, description='缓存')
    hidden = fields.BooleanField(default=False, description='是否隐藏')
    permission = fields.CharField(max_length=255, description='权限', null=True)
    is_menu = fields.BooleanField(default=False, description='是否为菜单')

    class Meta:
        table = 'oa_menu'

    def __str__(self):
        return self.title


class Dept(BaseModel):
    """
    反向和正向查询
    正向：dept.pid -->这是 父对象
    反向：dept.children.all() -->这是所有子部门对象，从父部门找它所有的子部门。
    """
    pid = fields.ForeignKeyField(model_name='models.Dept', description='父部门id', on_delete=fields.SET_NULL, null=True,
                                 related_name='children')
    sub_count = fields.IntField(description='子部门个数', null=True, blank=True)
    name = fields.CharField(max_length=64, description='部门名称', unique=True)
    enabled = fields.BooleanField(default=True, description='状态')
    dept_sort = fields.IntField(description='部门排序', null=True)

    class Meta:
        table = 'oa_dept'

    def __str__(self):
        return self.name


"""role负责查看这个是否为超级管理员，管理员可以查看那些菜单"""


class Role(BaseModel):
    name = fields.CharField(max_length=32, description='角色名', null=True, unique=True)
    level = fields.IntField(description='角色级别', null=True)
    description = fields.CharField(max_length=255, description='描述信息', null=True)
    data_scope = fields.CharField(max_length=32, description='权限描述，唯一编码', null=True)
    status = fields.BooleanField(default=True, description='是否为弃用状态')
    """
    depts（关联部门）： 通过 oa_roles_depts 中间表实现。
    用途： 规定这个角色“管辖”哪些部门。
    场景： “区域主管”这个角色可以关联“一号车间”和“二号车间”。

    menus（关联菜单）： 通过 oa_roles_menus 中间表实现。
    用途： 规定这个角色“能看到”哪些页面/按钮。
    场景： “维修工”角色关联了“故障查询”菜单，但没有“删除设备”菜单
    """
    depts = fields.ManyToManyField(model_name='models.Dept', through='oa_roles_dept', description='角色和部门关系')
    menus = fields.ManyToManyField(model_name='models.Menus', through='oa_roles_menus', description='角色和菜单关系')

    class Meta:
        table = 'ao_role'

    def __str__(self):
        return self.name


class Job(BaseModel):
    name = fields.CharField(max_length=64, description='岗位名称')
    enabled = fields.BooleanField(default=True, description='岗位状态')
    job_sort = fields.IntField(description='岗位排序', null=True)

    class Meta:
        table = 'oa_job'

    def __str__(self):
        return self.name


"""through相当于中间表
CREATE TABLE `oa_roles_menus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) NOT NULL COMMENT '对应 ao_role 表的 id',
  `menu_id` int(11) NOT NULL COMMENT '对应 oa_menu 表的 id',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_role_menu_role` FOREIGN KEY (`role_id`) REFERENCES `ao_role` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_role_menu_menu` FOREIGN KEY (`menu_id`) REFERENCES `oa_menu` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色和菜单关联中间表';
"""

"""

字段名说明校验规则mission_no任务单号唯一索引，
不可重复type任务类型1-入库 / 2-出库 / 3-移库status任务状态0, 1, 2, 3 整数映射from_loc起始库位必填to_loc目标库位必填operator操作人关联当前用户 ID
"""


# 仓库模型
class WMSWarehouse(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)  # 仓库名称
    code = fields.CharField(max_length=20, unique=True)  # 仓库编码：WH-A, WH-B
    rows = fields.IntField(default=10)  # 矩阵行
    cols = fields.IntField(default=10)  # 矩阵列
    is_active = fields.BooleanField(default=True)
    description = fields.TextField(null=True)

    class Meta:
        table = "wms_warehouse"


# 库位模型
class WMSLocation(models.Model):
    id = fields.IntField(pk=True)
    location_code = fields.CharField(max_length=50, unique=True)  # 唯一编号
    # 【核心改动】关联仓库对象
    warehouse = fields.ForeignKeyField('models.WMSWarehouse', related_name='locations')
    # 坐标信息
    row_index = fields.IntField(default=0)
    col_index = fields.IntField(default=0)
    # 状态：0-空闲, 1-占用, 2-锁定
    status = fields.IntField(default=0)
    # 【新增】库位类型：1-普通存储位, 2-收货区, 3-出货口
    location_type = fields.IntField(default=1)

    class Meta:
        table = "wms_location"


class wms_mission(BaseModel):
    mission_no = fields.CharField(max_length=64, unique=True, description="任务编号")
    type = fields.SmallIntField(default=1, description="1:入库, 2:出库, 3:移库")
    status = fields.SmallIntField(default=0, description="0:待处理, 1:执行中, 2:已完成, 3:异常")
    priority = fields.IntField(default=0, description="优先级")

    from_location = fields.ForeignKeyField('models.WMSLocation', related_name='missions_out', null=True)
    to_location = fields.ForeignKeyField('models.WMSLocation', related_name='missions_in', null=True)
    hardware_id = fields.CharField(max_length=4, index=True)
    device = fields.ForeignKeyField(
        'models.wms_device',
        related_name='missions',
        null=True,
        description="关联执行设备"
    )

    user = fields.ForeignKeyField(
        model_name='models.User',
        related_name='missions',  # 可以使用user.missions.all()，查询所欲的任务
        on_delete=fields.SET_NULL,
        null=True,
        description='创建者关联'
    )

    class Meta:
        table = "wms_mission"
        table_description = "仓储任务调度表"

    def __str__(self):
        return self.mission_no


# 设备表
class wms_device(BaseModel):
    device_code = fields.CharField(max_length=50, unique=True, description="设备唯一编号")
    device_type = fields.IntField(default=1, description="1:潜伏式AGV, 2:叉车")
    is_active = fields.BooleanField(default=True, description="是否启用")
    work_status = fields.IntField(default=0, description="0:空闲, 1:忙碌, 2:故障")
    battery = fields.IntField(default=100, description="电量")

    class Meta:
        # 这里定义数据库中实际生成的表名
        table = "wms_device"
        table_description = "设备信息表"

    def __str__(self):
        return self.device_code

# class WMSUser(BaseModel):
#     id = fields.IntField(pk=True)
#     username = fields.CharField(max_length=50, unique=True, description="登录账号")
#     password = fields.CharField(max_length=128, description="加密密码")
#     full_name = fields.CharField(max_length=50, null=True, description="真实姓名")
#     role = fields.IntField(default=1, description="角色: 1-操作员, 2-管理员")
#     is_active = fields.BooleanField(default=True, description="是否启用")
#
#     class Meta:
#         table = "wms_user"
