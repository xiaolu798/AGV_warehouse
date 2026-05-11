from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `oa_users` MODIFY COLUMN `nick_name` VARCHAR(32) COMMENT '用户昵称';
        ALTER TABLE `oa_users` ADD UNIQUE INDEX `nick_name` (`nick_name`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `oa_users` DROP INDEX `nick_name`;
        ALTER TABLE `oa_users` MODIFY COLUMN `nick_name` VARCHAR(32) NOT NULL COMMENT '用户昵称';"""


MODELS_STATE = (
    "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"
    "834p08vT/+Ik6Ug="
)
