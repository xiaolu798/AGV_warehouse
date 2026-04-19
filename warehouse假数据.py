import asyncio

from tortoise import Tortoise

from src.apps.system.models import *
from src.utils.common_db import TORTOISE_ORM


async def seed():
    # 1. 连接数据库（替换成你自己的数据库配置）
    await Tortoise.init(config=TORTOISE_ORM)

    # 2. 创建仓库 A
    wh, _ = await WMSWarehouse.get_or_create(
        code="WH-A",
        defaults={"name": "自动化1号仓", "rows": 5, "cols": 10, "description": "测试大屏专用"}
    )

    # 3. 批量生成 50 个库位
    locations = []
    for r in range(wh.rows):
        for c in range(wh.cols):
            loc_code = f"A-{r + 1:02d}-{c + 1:02d}"
            # 模拟：让前两排有货 (status=1)，其他的为空闲 (status=0)
            initial_status = 1 if r < 2 else 0

            locations.append(WMSLocation(
                location_code=loc_code,
                warehouse=wh,
                row_index=r,
                col_index=c,
                status=initial_status,
                location_type=1
            ))

    # 清空旧库位并重新插入
    await WMSLocation.filter(warehouse=wh).delete()
    await WMSLocation.bulk_create(locations)

    print(f"数据生成成功！仓库: {wh.name}, 已生成 {len(locations)} 个库位。")


if __name__ == "__main__":
    asyncio.run(seed())
