import asyncio

from tortoise import Tortoise

from src.apps.system.models import wms_device
from src.utils.common_db import TORTOISE_ORM


async def init_fake_devices():
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        devices_to_create = []

        # 批量生成 50 台 AGV
        for i in range(1, 51):
            code = f"AGV-{str(i).zfill(3)}"  # 生成 AGV-001 到 AGV-050

            # 模拟随机电量 (20% - 100%)
            import random
            battery_val = random.randint(20, 100)

            # 模拟初始状态：大部分空闲(0)，少量忙碌(1)，极个别故障(2)
            rand_val = random.random()
            if rand_val > 0.95:
                status = 2  # 5% 概率故障
                active = False
            elif rand_val > 0.7:
                status = 1  # 25% 概率忙碌
                active = True
            else:
                status = 0  # 70% 概率空闲
                active = True

            devices_to_create.append(
                wms_device(
                    device_code=code,
                    device_type=1,  # 1 代表标准 AGV
                    work_status=status,
                    battery=battery_val,
                    is_active=active
                )
            )

        # 使用 bulk_create 提高写入速度
        await wms_device.bulk_create(devices_to_create)
        print(f"成功初始化 {len(devices_to_create)} 台设备数据！")

    except Exception as e:
        print(f"数据初始化失败: {e}")

if __name__ == "__main__":
    asyncio.run(init_fake_devices())
