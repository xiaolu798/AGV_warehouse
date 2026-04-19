from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `wms_device` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `device_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '设备唯一编号',
    `device_type` INT NOT NULL COMMENT '1:潜伏式AGV, 2:叉车' DEFAULT 1,
    `is_active` BOOL NOT NULL COMMENT '是否启用' DEFAULT 1,
    `work_status` INT NOT NULL COMMENT '0:空闲, 1:忙碌, 2:故障' DEFAULT 0,
    `battery` INT NOT NULL COMMENT '电量' DEFAULT 100
) CHARACTER SET utf8mb4 COMMENT='设备信息表';
        ALTER TABLE `wms_mission` ADD `device_id` INT COMMENT '关联执行设备';
        ALTER TABLE `wms_mission` DROP COLUMN `device_code`;
        ALTER TABLE `wms_mission` ADD CONSTRAINT `fk_wms_miss_wms_devi_bbcf5ead` FOREIGN KEY (`device_id`) REFERENCES `wms_device` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `wms_mission` DROP FOREIGN KEY `fk_wms_miss_wms_devi_bbcf5ead`;
        ALTER TABLE `wms_mission` ADD `device_code` VARCHAR(50) COMMENT '设备编号';
        ALTER TABLE `wms_mission` DROP COLUMN `device_id`;
        DROP TABLE IF EXISTS `wms_device`;"""


MODELS_STATE = (
    "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"
)
