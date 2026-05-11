from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `wms_warehouse` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `rows` INT NOT NULL DEFAULT 10,
    `cols` INT NOT NULL DEFAULT 10,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `description` LONGTEXT
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `wms_location` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `location_code` VARCHAR(50) NOT NULL UNIQUE,
    `row_index` INT NOT NULL DEFAULT 0,
    `col_index` INT NOT NULL DEFAULT 0,
    `status` INT NOT NULL DEFAULT 0,
    `location_type` INT NOT NULL DEFAULT 1,
    `warehouse_id` INT NOT NULL,
    CONSTRAINT `fk_wms_loca_wms_ware_aee22d1a` FOREIGN KEY (`warehouse_id`) REFERENCES `wms_warehouse` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        ALTER TABLE `wms_mission` ADD `to_location_id` INT;
        ALTER TABLE `wms_mission` ADD `hardware_id` VARCHAR(4) NOT NULL;
        ALTER TABLE `wms_mission` ADD `from_location_id` INT;
        ALTER TABLE `wms_mission` DROP COLUMN `from_location`;
        ALTER TABLE `wms_mission` DROP COLUMN `to_location`;
        ALTER TABLE `wms_mission` MODIFY COLUMN `mission_no` VARCHAR(64) NOT NULL COMMENT '任务编号';
        ALTER TABLE `wms_mission` ADD CONSTRAINT `fk_wms_miss_wms_loca_caa7c993` FOREIGN KEY (`from_location_id`) REFERENCES `wms_location` (`id`) ON DELETE CASCADE;
        ALTER TABLE `wms_mission` ADD CONSTRAINT `fk_wms_miss_wms_loca_7ab63e2f` FOREIGN KEY (`to_location_id`) REFERENCES `wms_location` (`id`) ON DELETE CASCADE;
        ALTER TABLE `wms_mission` ADD INDEX `idx_wms_mission_hardwar_b0474f` (`hardware_id`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `wms_mission` DROP INDEX `idx_wms_mission_hardwar_b0474f`;
        ALTER TABLE `wms_mission` DROP FOREIGN KEY `fk_wms_miss_wms_loca_7ab63e2f`;
        ALTER TABLE `wms_mission` DROP FOREIGN KEY `fk_wms_miss_wms_loca_caa7c993`;
        ALTER TABLE `wms_mission` ADD `from_location` VARCHAR(100) COMMENT '起始库位';
        ALTER TABLE `wms_mission` ADD `to_location` VARCHAR(100) COMMENT '目标库位';
        ALTER TABLE `wms_mission` DROP COLUMN `to_location_id`;
        ALTER TABLE `wms_mission` DROP COLUMN `hardware_id`;
        ALTER TABLE `wms_mission` DROP COLUMN `from_location_id`;
        ALTER TABLE `wms_mission` MODIFY COLUMN `mission_no` VARCHAR(50) NOT NULL COMMENT '任务编号';
        DROP TABLE IF EXISTS `wms_warehouse`;
        DROP TABLE IF EXISTS `wms_location`;"""


MODELS_STATE = (
    "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"
    "=="
)
