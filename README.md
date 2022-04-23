# djang_admin_backend

# 使用说明
   * **根目录下面需要创建一个log文件夹**
   * **复制conf文件夹里面的env_example.py到conf文件夹下面并重命名为env.py**
   * **执行 pip install -r requirements.txt(最好使用虚拟环境  anaconda)**
   * **执行 python manage.py makemigrations**
   * **执行 python manage.py migrate**
   * **执行 python manage.py createsuperuser  创建超级用户**
   * **执行 python manage.py runserver**

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

    |-- account   # 账号管理模块
    |   |-- admin.py
    |   |-- apps.py
    |   |-- models.py
    |   |-- tests.py
    |   |-- views.py
    |   |-- __init__.py
    |   |-- migrations
    |   |   |-- __init__.py
    |   |-- rest
    |   |   |-- api.py
    |   |   |-- filters.py
    |   |   |-- serializers.py
    |   |   |-- urls.py

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



# yapf使用教程
  
   ## 安装
    pip install yapf  注意这个不是在项目pip里面安装 而是要在自己电脑环境的pip里面安装
    
   ## 脚本文件
    在项目根目录下的yapf_script.txt

   ## 使用方法
    将yapf_script.txt文件放到.git/hooks/post-commit中  这里的post-commit要自己手动创建 然后就可以使用yapf了
    
   