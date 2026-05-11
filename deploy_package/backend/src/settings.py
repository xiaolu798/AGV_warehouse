"""
借助于：pydantic + dotenv -->动态的初始化排至文件
-开发阶段使用一套
-上限阶段使用一套
"""
# # 配置文件
# class AppConfig:
#     APP_HOST = '127.0.0.1'
#     APP_PORT = 8000
#
#
# setting = AppConfig()

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path


class AppConfig(BaseSettings):
    APP_HOST: str = '0.0.0.0'
    APP_PORT: int = 8080
    BASE_DIR: Path = Path(__file__).parent.parent

    DB_HOST: str = 'mysql'
    DB_PORT: int = 3306
    DB_USER: str = 'agv'
    DB_PASSWORD: str = 'agv123456'
    DB_NAME: str = 'oa_backend'
    DB_MIN_SIZE: int = 1
    DB_MAX_SIZE: int = 10
    DB_CHARSET: str = 'utf8mb4'

    HARDWARE_HOST: str = '0.0.0.0'
    HARDWARE_PORT: int = 13245

    # jwt
    ACCESS_TOKEN_expire_time: int = 30
    SERCERT_KEY: str = 'UvTnskOo24uZ0FJApFVXO4d3HH1Xrysd'
    ALGORITHMS: str = 'HS256'


load_dotenv(Path(__file__).parent.parent / '.envs')
setting = AppConfig()
