# -*- coding: utf-8 -*-
"""
    @Time ： 2022/4/19 16:55
    @Auth ： wangzw
    @File ：env_example.py
    @IDE ：PyCharm
    @Motto：ABC(Always Be Coding)
"""
import os

from dj_admin_backend.settings import BASE_DIR

DATABASE_ENGINE = "django.db.backends.sqlite3"
# 数据库名
DATABASE_NAME = os.path.join(BASE_DIR, 'db.sqlite3')
# 数据库地址 改为自己数据库地址
DATABASE_HOST = "127.0.0.1"
# 数据库端口
DATABASE_PORT = 3306
# 数据库用户名
DATABASE_USER = "root"
# 数据库密码
DATABASE_PASSWORD = "123456"