from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `oa_dept` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `sub_count` INT COMMENT '子部门个数',
    `name` VARCHAR(64) NOT NULL UNIQUE COMMENT '部门名称',
    `enabled` BOOL NOT NULL COMMENT '状态' DEFAULT 1,
    `dept_sort` INT COMMENT '部门排序',
    `pid_id` INT COMMENT '父部门id',
    CONSTRAINT `fk_oa_dept_oa_dept_e8b89e44` FOREIGN KEY (`pid_id`) REFERENCES `oa_dept` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `oa_job` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `name` VARCHAR(64) NOT NULL COMMENT '岗位名称',
    `enabled` BOOL NOT NULL COMMENT '岗位状态' DEFAULT 1,
    `job_sort` INT COMMENT '岗位排序'
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `oa_menu` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `sub_count` INT COMMENT '子菜单数目',
    `type` INT COMMENT '菜单类型',
    `title` VARCHAR(32) UNIQUE COMMENT '菜单标题',
    `name` VARCHAR(255) UNIQUE COMMENT '前端组件名称',
    `component` VARCHAR(255) COMMENT '前端组件',
    `menu_sort` INT COMMENT '菜单排序',
    `icon` VARCHAR(255) COMMENT '菜单图标',
    `path` VARCHAR(255) COMMENT '菜单连接地址',
    `i_frame` BOOL NOT NULL COMMENT '是否外链' DEFAULT 0,
    `cache` BOOL NOT NULL COMMENT '缓存' DEFAULT 0,
    `hidden` BOOL NOT NULL COMMENT '是否隐藏' DEFAULT 0,
    `permission` VARCHAR(255) COMMENT '权限',
    `is_menu` BOOL NOT NULL COMMENT '是否为菜单' DEFAULT 0,
    `pid_id` INT COMMENT '父菜单id',
    CONSTRAINT `fk_oa_menu_oa_menu_393bc584` FOREIGN KEY (`pid_id`) REFERENCES `oa_menu` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `ao_role` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `name` VARCHAR(32) UNIQUE COMMENT '角色名',
    `level` INT COMMENT '角色级别',
    `description` VARCHAR(255) COMMENT '描述信息',
    `data_scope` VARCHAR(32) COMMENT '权限描述，唯一编码',
    `status` BOOL NOT NULL COMMENT '是否为弃用状态' DEFAULT 1
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `oa_users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `username` VARCHAR(255) NOT NULL COMMENT '用户名',
    `password` VARCHAR(128) NOT NULL COMMENT '用户密码',
    `avatar` VARCHAR(255) NOT NULL COMMENT '头像' DEFAULT 'avatar/default.png',
    `is_active` BOOL NOT NULL COMMENT '是否为活跃用户' DEFAULT 1,
    `email` VARCHAR(32) COMMENT '邮箱',
    `nick_name` VARCHAR(32) NOT NULL COMMENT '用户昵称',
    `gender` VARCHAR(16) COMMENT '性别',
    `phone` VARCHAR(11) UNIQUE COMMENT '电话号码',
    `enabled` BOOL NOT NULL COMMENT '是否弃用？状态:1启用、0禁用' DEFAULT 1,
    `is_superuser` BOOL NOT NULL COMMENT '是否为超级用户' DEFAULT 0,
    `dept_id` INT COMMENT '部门名字',
    CONSTRAINT `fk_oa_users_oa_dept_552eab7d` FOREIGN KEY (`dept_id`) REFERENCES `oa_dept` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `online_user` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `create_time` DATETIME(6) COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `update_time` DATETIME(6) COMMENT '更新找时间' DEFAULT CURRENT_TIMESTAMP(6),
    `create_by` VARCHAR(32) COMMENT '创建者',
    `update_by` VARCHAR(32) COMMENT '更新着',
    `is_delete` BOOL NOT NULL COMMENT '是否删除' DEFAULT 0,
    `brower` VARCHAR(255) NOT NULL COMMENT '用户登录浏览器',
    `ip` VARCHAR(64) COMMENT '用户登录IP',
    `key` VARCHAR(255) COMMENT '用户token',
    `user_id` INT,
    CONSTRAINT `fk_online_u_oa_users_523dc94d` FOREIGN KEY (`user_id`) REFERENCES `oa_users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `oa_roles_dept` (
    `ao_role_id` INT NOT NULL,
    `dept_id` INT NOT NULL,
    FOREIGN KEY (`ao_role_id`) REFERENCES `ao_role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`dept_id`) REFERENCES `oa_dept` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_oa_roles_de_ao_role_c703c4` (`ao_role_id`, `dept_id`)
) CHARACTER SET utf8mb4 COMMENT='角色和部门关系';
CREATE TABLE IF NOT EXISTS `oa_roles_menus` (
    `ao_role_id` INT NOT NULL,
    `menus_id` INT NOT NULL,
    FOREIGN KEY (`ao_role_id`) REFERENCES `ao_role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`menus_id`) REFERENCES `oa_menu` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_oa_roles_me_ao_role_693b6e` (`ao_role_id`, `menus_id`)
) CHARACTER SET utf8mb4 COMMENT='角色和菜单关系';
CREATE TABLE IF NOT EXISTS `oa_users_job` (
    `oa_users_id` INT NOT NULL,
    `job_id` INT NOT NULL,
    FOREIGN KEY (`oa_users_id`) REFERENCES `oa_users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`job_id`) REFERENCES `oa_job` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_oa_users_jo_oa_user_c523e6` (`oa_users_id`, `job_id`)
) CHARACTER SET utf8mb4 COMMENT='岗位名称';
CREATE TABLE IF NOT EXISTS `oa_users_role` (
    `oa_users_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    FOREIGN KEY (`oa_users_id`) REFERENCES `oa_users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `ao_role` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_oa_users_ro_oa_user_1b27eb` (`oa_users_id`, `role_id`)
) CHARACTER SET utf8mb4 COMMENT='用户和角色的关联表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "+kuZXp7+B/GR6ik="
)
