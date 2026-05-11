import time

from fastapi import APIRouter, Depends
from src.apps.system.models import *
from src.apps.system.schwmas import *
from src.apps.system.views.user import access_token
from src.utils.common_response import APIResponse
from src.utils.ws_connetc import ws_manager
import uuid
from tortoise.transactions import in_transaction
import datetime

router = APIRouter()


# 获取所有任务清单
@router.get('/mission/', description='查询所有的')
async def get_task_list(user: User = Depends(access_token)):
    # MissionOutSchema 里库位还会继续读取 warehouse，因此这里把二级关联一起预加载
    task_obj = await wms_mission.filter(user=user) \
        .order_by("-create_time") \
        .prefetch_related('from_location__warehouse', 'to_location__warehouse', 'device') \
        .all()

    # 转化为 Pydantic 模型
    result = [MissionOutSchema.model_validate(task).model_dump() for task in task_obj]
    return APIResponse(result=result)


# 创建任务清单
@router.post('/mission/', description='创建一个任务清单')
async def create_task(task: MissionCreateSchema, user: User = Depends(access_token)):
    # 1. 生成唯一业务编号与硬件通讯 ID
    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    uid_suffix = uuid.uuid4().hex[:8]
    mission_no = f"Task{time_str}{uid_suffix}"
    hardware_id = str(int(time.time() * 1000) % 10000).zfill(4)

    # 2. 获取并校验库位对象
    start_node = await WMSLocation.get_or_none(location_code=task.from_location)
    end_node = await WMSLocation.get_or_none(location_code=task.to_location)

    if not start_node or start_node.status != 1:
        return APIResponse(code=400, msg="起点库位无货或不存在")
    if not end_node or end_node.status != 0:
        return APIResponse(code=400, msg="目标库位已被占用或不存在")

    # 3. 使用事务处理：锁定库位并生成任务
    async with in_transaction():
        # 锁定库位（status=2）
        start_node.status = 2
        end_node.status = 2
        await start_node.save()
        await end_node.save()

        # 处理 Schema 数据：弹出字符串类型的同名键，确保外键对象能正确写入
        data_obj = task.model_dump()
        data_obj.pop('from_location', None)
        data_obj.pop('to_location', None)

        # 创建任务清单
        new_mission = await wms_mission.create(
            **data_obj,
            mission_no=mission_no,
            user=user,
            status=0,
            hardware_id=hardware_id,
            from_location=start_node,  # 传入 ORM 对象
            to_location=end_node  # 传入 ORM 对象
        )

    return APIResponse(msg='任务创建成功', result={"mission_no": mission_no})


class MissionAssignSchema(BaseModel):
    mission_id: int  # <--- 你要的 ID 在这里
    device_code: Optional[str] = None


# 获取清单，进行修改任务清单状态和分配设备码
@router.post('/mission/assign', description='领取任务')
async def assign_mission(data: MissionAssignSchema):
    # 1. 先只根据 ID 查任务，判断“存在性”
    task = await wms_mission.get_or_none(id=data.mission_id)

    if not task:
        return APIResponse(code=404, msg='任务不存在')

    # 2. 获取并校验设备
    device = await wms_device.get_or_none(device_code=data.device_code, is_active=True)
    if not device or device.work_status != 0:
        return APIResponse(code=400, msg='设备忙碌或异常')
    update_data = {
        "status": 1,  # 变更为执行中
        "device": device,
    }
    await task.update_from_dict(update_data)
    await task.save()
    # 4. 【重要】更新设备状态为忙碌
    device.work_status = 1
    await device.save()
    # 5. WebSocket 广播：建议带上库位信息，方便大屏渲染“作业路径”
    # 记得先预加载库位数据，否则广播里拿不到库位代码
    await task.fetch_related('from_location', 'to_location')

    await ws_manager.broadcast({
        "event": "update_status",
        "data": {
            "mission_id": task.id,
            "device_code": device.device_code,
            "from_location": task.from_location.location_code,  # 方便大屏高亮起点
            "to_location": task.to_location.location_code,  # 方便大屏高亮终点
            "work_status": 1,
            "task_status": 1
        }
    })
    return APIResponse(msg='任务领取成功，正在执行中')


# 任务完成
# 任务完成接口
@router.post('/mission/finish', description='任务完成')
async def mission_finish(data: MissionAssignSchema):
    # 使用 get_or_none 确保拿到的是对象而不是列表
    task = await wms_mission.get_or_none(id=data.mission_id).prefetch_related('device')

    if not task:
        return APIResponse(code=404, msg='任务不存在')

    # 规则 1：校验状态
    if task.status != 1:
        status_map = {0: "待处理", 2: "已完成", 3: "异常"}
        current_status = status_map.get(task.status, "未知")
        return APIResponse(code=400, msg=f'任务当前处于[{current_status}]状态，无法点击完成')

    # 使用事务保证两张表同时更新成功
    async with in_transaction():
        # 规则 2：释放关联的设备
        device_code = task.device.device_code if task.device else ""
        if task.device:
            task.device.work_status = 0
            await task.device.save()
        # 2. 【新增】处理库位状态转移
        if task.from_location:
            task.from_location.status = 0  # 起点变空闲
            await task.from_location.save()

        if task.to_location:
            task.to_location.status = 1  # 终点变占用
            await task.to_location.save()

        # 规则 3：更新任务状态为已完成
        task.status = 2
        await task.save()

    await ws_manager.broadcast({
        "event": "update_status",
        "data": {
            "mission_id": task.id,
            "device_code": device_code,
            "work_status": 0,
            "task_status": 2,
        }
    })

    return APIResponse(msg='任务已顺利完成，设备已释放')


# 任务的删除
@router.post('/mission/cancel', description='任务未执行时撤销')
async def cancel_mission(data: MissionAssignSchema):
    # 1. 查询任务并预加载关联库位
    task = await wms_mission.get_or_none(id=data.mission_id).prefetch_related('from_location', 'to_location')

    if not task:
        return APIResponse(code=404, msg='任务不存在')

    # 2. 只有待处理(0)的任务可以撤销
    if task.status != 0:
        status_map = {1: "执行中", 2: "已完成", 3: "异常", -1: "已取消"}
        current_status = status_map.get(task.status, "未知")
        return APIResponse(code=400, msg=f'任务处于[{current_status}]状态，无法撤销')

    # 3. 使用事务：回滚库位状态并更新任务
    async with in_transaction():
        # 起点：既然不搬了，状态从“锁定”恢复为“占用/有货” (1)
        if task.from_location:
            task.from_location.status = 1
            await task.from_location.save()

        # 终点：既然货不来了，状态从“锁定”恢复为“空闲” (0)
        if task.to_location:
            task.to_location.status = 0
            await task.to_location.save()

        # 更新任务状态为已取消 (-1)
        task.status = -1
        await task.save()

    return APIResponse(msg='任务已成功撤销，库位状态已恢复')


@router.get('/devices/', description='查询所有设备状态')
async def get_devices_list():
    # 返回设备编号、类型、工作状态(0空闲/1忙碌/2故障)
    """
    前端页面展示设备状态大屏时调用
    """
    devices = await wms_device.all().order_by("-work_status", "device_code")
    result = [DeviceSchema.model_validate(device).model_dump() for device in devices]

    return APIResponse(result=result)


@router.post('/devices/status', description='手动切换设备状态')
async def update_device_status(device_id: int, status: int):
    """
    用于人工干预：例如某台机器修好了，手动从“故障”改为“空闲”
    """
    device = await wms_device.get_or_none(id=device_id)
    if not device:
        return APIResponse(code=404, msg='设备不存在')

    device.work_status = status
    await device.save()
    return APIResponse(msg='设备状态更新成功')


@router.delete('/devices/{device_id}', description='删除/停用设备')
async def delete_device(device_id: int):
    device = await wms_device.get_or_none(id=device_id)
    if device:
        # 如果设备正在执行任务，禁止删除
        if device.work_status == 1:
            return APIResponse(code=400, msg='设备正在执行任务中，无法删除')

        await device.delete()
        return APIResponse(msg='设备已移除')
    return APIResponse(code=404, msg='未找到该设备')


# 获取所有的仓库
# 修改 get_house_list
@router.get('/warehouse', description='仓库列表')
async def get_house_list():
    warehouses = await WMSWarehouse.all().prefetch_related('locations')

    results = []
    for w in warehouses:
        data = WMSWarehouseSchema.model_validate(w).model_dump()
        # 实时计算库位状态
        locs = list(w.locations)
        data['total_slots'] = len(locs)
        data['used_slots'] = len([l for l in locs if l.status == 1])
        results.append(data)

    return APIResponse(result=results)


# 创建仓库并自动初始化仓库的库位
@router.post('/warehouse', description='创建仓库并自动初始化库位矩阵')
async def create_warehouse_and_init(data: WarehouseCreateSchema, user: User = Depends(access_token)):
    # 1. 校验编码唯一性
    if await WMSWarehouse.exists(code=data.code):
        return APIResponse(code=400, msg="仓库编码已存在")

    try:
        async with in_transaction():
            # 2. 第一步：创建仓库实体（拿到 rows 和 cols）
            new_wh = await WMSWarehouse.create(
                name=data.name,
                code=data.code,
                rows=data.rows,
                cols=data.cols,
                description=data.description
            )

            # 3. 第二步：根据 rows/cols 自动生成库位对象列表
            locations_to_create = []
            for r in range(new_wh.rows):
                for c in range(new_wh.cols):
                    # 自动生成编号：仓库码-行-列 (如 WH-A-01-05)
                    loc_code = f"{new_wh.code}-{r + 1:02d}-{c + 1:02d}"

                    locations_to_create.append(WMSLocation(
                        location_code=loc_code,
                        warehouse=new_wh,  # 关联刚创建的仓库对象
                        row_index=r,  # 物理行坐标
                        col_index=c,  # 物理列坐标
                        status=0,  # 默认空闲
                        location_type=1  # 默认普通库位
                    ))

            # 4. 第三步：利用 bulk_create 性能最优地写入数据库
            await WMSLocation.bulk_create(locations_to_create)

        return APIResponse(msg=f"仓库 {new_wh.name} 创建成功，并已自动生成 {len(locations_to_create)} 个库位")

    except Exception as e:
        # 事务会自动回滚
        return APIResponse(code=500, msg=f"创建失败: {str(e)}")


# 获取仓库矩阵详情 (供前端大屏使用)
@router.get('/warehouse/{id}/matrix', description='获取仓库完整矩阵详情')
async def get_warehouse_matrix(id: int):
    # prefetch_related 会一次性查出所有关联的库位，避免 N+1 查询问题
    warehouse = await WMSWarehouse.get_or_none(id=id).prefetch_related('locations')

    if not warehouse:
        return APIResponse(code=404, msg="仓库不存在")

    # 格式化库位数据
    loc_data = [
        {
            "id": loc.id,
            "code": loc.location_code,
            "r": loc.row_index,
            "c": loc.col_index,
            "status": loc.status
        } for loc in warehouse.locations
    ]

    return APIResponse(result={
        "info": WMSWarehouseSchema.model_validate(warehouse).model_dump(),
        "matrix": loc_data
    })

