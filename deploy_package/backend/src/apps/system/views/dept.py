from fastapi import APIRouter, Depends
from src.apps.system.models import *
from src.apps.system.schwmas import *
from src.apps.system.views.user import access_token
from src.utils.common_response import APIResponse
from tortoise.transactions import in_transaction

router = APIRouter()


# 查询所有部门
@router.get('/depts', description='查询所有的部门')
async def get_dept_list(user: User = Depends(access_token)):
    # 加上过滤条件，只查出父部门
    all_depts = await Dept.filter(is_delete=False).order_by('dept_sort').all()

    # 第二步：调用同步的内存组装方法
    dept_tree = DeptSchemas.build_tree(all_depts)

    # 第三步：直接返回结果
    return APIResponse(result=dept_tree)


# 查询一个部门（用于编辑回显）
@router.get('/depts/{dept_id}', description='查询一个部门')
async def get_dept(dept_id: int, user: User = Depends(access_token)):
    dept_obj = await Dept.filter(is_delete=False, id=dept_id).first()
    if not dept_obj:
        return APIResponse(code=404, msg='部门不存在')

    # 1. 先验证并转化为 Pydantic 模型
    schema_obj = DeptInSchema.model_validate(dept_obj)

    # 2. 关键：将模型实例导出为普通的 Python 字典，这样 APIResponse 才能序列化它
    result = schema_obj.model_dump()

    return APIResponse(result=result)


# 新增部门
@router.post('/depts', description='新增一个部门')
async def add_dept(dept_in: DeptInSchema, user: User = Depends(access_token)):
    async with in_transaction():
        # 1. 提取数据
        data = dept_in.model_dump()

        # 2. 创建部门 (因为你的 Schema 字段名已经是 pid_id，这步会直接生效)
        new_dept = await Dept.create(**data)

        # 3. 更新父部门计数 (注意这里的字段取值)
        pid_id = data.get('pid_id')
        if pid_id:
            parent = await Dept.get_or_none(id=pid_id)
            if parent:
                parent.sub_count = (parent.sub_count or 0) + 1
                await parent.save()

        return APIResponse(msg='新增部门成功')


# 删除某个部门
@router.delete('/depts/{dept_id}', description='删除某个部门')
async def delete_dept(dept_id: int, user: User = Depends(access_token)):
    # 使用事务确保数据一致性（删除部门和更新父级计数要么全成功，要么全失败）
    async with in_transaction():
        # 1. 查询该部门是否存在
        dept_obj = await Dept.get_or_none(id=dept_id)
        if not dept_obj:
            return APIResponse(code=404, msg='部门不存在')

        # 2. 获取父部门对象（通过外键关联获取）
        # 注意：dept_obj.pid 在 Tortoise 中是一个异步属性或预加载对象
        parent_dept = await dept_obj.pid

        # 3. 执行删除操作
        # 此时：数据库会自动将该部门下所有子部门的 pid 设置为 NULL (因为 SET_NULL)
        await dept_obj.delete()

        # 4. 如果存在父部门，更新父部门的 sub_count
        if parent_dept:
            # 确保计数不小于 0
            new_count = max(0, (parent_dept.sub_count or 1) - 1)
            parent_dept.sub_count = new_count
            await parent_dept.save()

        return APIResponse(msg='删除部门成功')


# 更新一个部门字段（用于编辑提交）
@router.put('/depts/{dept_id}', description='更新部门')
async def update_dept(
        dept_id: int,
        dept_in: DeptInSchema,
        user: User = Depends(access_token)
):
    async with in_transaction():
        dept_obj = await Dept.get_or_none(id=dept_id, is_delete=False)
        if not dept_obj:
            return APIResponse(code=404, msg='部门不存在')

        update_data = dept_in.model_dump(exclude={'sub_count'})
        await dept_obj.update_from_dict(update_data)
        await dept_obj.save()

        return APIResponse(msg='更新部门成功')
