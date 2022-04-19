# djang_admin_backend
about python3.8 + django 3.2.9

# 文件结构树
    |-- app_template   # 应用模板  用来快速生成app模板
    |   |-- admin.py-tpl
    |   |-- apps.py-tpl
    |   |-- models.py-tpl
    |   |-- tests.py-tpl
    |   |-- views.py-tpl
    |   |-- __init__.py-tpl
    |   |-- migrations
    |   |   |-- __init__.py-tpl
    |   |-- rest
    |       |-- api.py-tpl
    |       |-- filters.py-tpl
    |       |-- serializers.py-tpl
    |       |-- urls.py-tpl

    |-- common   # 工具类
    |   |-- admin.py
    |   |-- apps.py
    |   |-- auth.py
    |   |-- docs.py
    |   |-- exception_handler.py  # 全局异常处理
    |   |-- logger.py  # 日志文件
    |   |-- models.py
    |   |-- pagination.py  # 分页封装
    |   |-- tests.py
    |   |-- views.py
    |   |-- __init__.py
    |   |-- migrations
    |   |   |-- __init__.py

    |   |-- rest
    |   |   |-- api.py  # 所有rest api
    |   |   |-- filters.py # 所有rest api的过滤器
    |   |   |-- serializers.py # 所有rest api的序列化器
    |   |   |-- urls.py # 所有rest api的url

    |-- conf # 配置文件
    |   |-- env.py  # 环境变量(这个要自己复制一份 env.py.example)
    |   |-- env_example.py # 环境变量示例

    |-- dj_admin_backend
    |   |-- asgi.py
    |   |-- settings.py
    |   |-- urls.py  # 后端urls
    |   |-- wsgi.py
    |   |-- __init__.py

    |-- log        #日志文件
        |-- biz.log
        |-- main.log
        |-- trade.log
        |-- .gitignore

    |-- .style.yapf  # 格式化代码 需要安装yapf
    |-- db.sqlite3 
    |-- manage.py
    |-- README.md
    |-- requirements.txt  # 依赖包文件
    |-- startapp.py  # 创建app   python startapp.py app_name 根据上面的app_template模板创建app


