from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `wms_mission` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `mission_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '任务编号',
    `type` SMALLINT NOT NULL COMMENT '1:入库, 2:出库, 3:移库' DEFAULT 1,
    `status` SMALLINT NOT NULL COMMENT '0:待处理, 1:执行中, 2:已完成, 3:异常' DEFAULT 0,
    `priority` INT NOT NULL COMMENT '优先级' DEFAULT 0,
    `from_location` VARCHAR(100) COMMENT '起始库位',
    `to_location` VARCHAR(100) COMMENT '目标库位',
    `device_code` VARCHAR(50) COMMENT '设备编号'
) CHARACTER SET utf8mb4 COMMENT='仓储任务调度表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `wms_mission`;"""


MODELS_STATE = (
    "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"
    "DeXRz/t4rr6fnVSZVXhAucDD28PP8fA3e6Zw=="
)
