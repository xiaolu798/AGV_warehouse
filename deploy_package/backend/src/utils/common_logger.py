from loguru import logger
from src.settings import setting


def get_logger():
    # 1. 确保 logs 目录存在
    log_path = setting.BASE_DIR.joinpath("logs")
    log_path.mkdir(parents=True, exist_ok=True)

    # 2. 配置 INFO 级别日志
    # 使用 {time} 占位符，Loguru 会自动根据当前时间命名文件
    log_info_name = log_path.joinpath("info_{time:YYYY-MM-DD}.log")
    logger.add(
        str(log_info_name),
        level="INFO",
        rotation="00:00",  # 每天凌晨 00:00 创建新文件
        retention="3 days",  # 保留 3 天
        encoding="utf-8",
        enqueue=True,  # 异步写入，在高并发下保护性能
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )

    # 3. 配置 ERROR 级别日志
    log_error_name = log_path.joinpath("error_{time:YYYY-MM-DD}.log")
    logger.add(
        str(log_error_name),
        level="ERROR",
        rotation="00:00",
        retention="4 weeks",  # 保留 4 个星期
        encoding="utf-8",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )

    return logger


# 在工厂函数或 main.py 中调用一次即可
log = get_logger()
