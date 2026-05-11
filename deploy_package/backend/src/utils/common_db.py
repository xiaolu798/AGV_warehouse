from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from src.settings import setting

TORTOISE_ORM = {
    'connections': {
        'default': {
            'engine': 'tortoise.backends.mysql',  # MySQL or Mariadb
            'credentials': {
                'host': setting.DB_HOST,
                'port': setting.DB_PORT,
                'user': setting.DB_USER,
                'password': setting.DB_PASSWORD,
                'database': setting.DB_NAME,
                'minsize': setting.DB_MIN_SIZE,
                'maxsize': setting.DB_MAX_SIZE,
                'charset': setting.DB_CHARSET,
            }
        },
    },
    # "connections": {"default": "mysql://root:1234@127.0.0.1:3306/fastapi"},
    'apps': {
        'models': {
            # models:models 找到对应自定义的model.py
            'models': ['src.apps.system.models', "aerich.models"],  # aerich.models迁移模型
            'default_connection': 'default',
        }
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}


def register_mysql(app: FastAPI):
    register_tortoise(app, config=TORTOISE_ORM)
