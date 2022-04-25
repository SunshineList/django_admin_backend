from django.db import models


# Create your models here.
class OperationLog(models.Model):
    GET = 'GET'
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

    OPERATION_TYPE = (
        (GET, '查询'),
        (POST, "新增"),
        (PUT, "更新"),
        (DELETE, "删除")
    )

    operation_user = models.ForeignKey('account.UsersModel', on_delete=models.CASCADE, verbose_name='操作用户',
                                       related_name='op_user', null=True, blank=True)
    operation_type = models.CharField("操作类型", max_length=10, null=True, blank=True, choices=OPERATION_TYPE)
    operation_path = models.CharField("操作路径", max_length=100, null=True, blank=True)
    operation_modular = models.CharField(max_length=64, verbose_name="请求模块", null=True, blank=True, help_text="请求模块")
    operation_params = models.TextField("请求参数", null=True, blank=True)
    operation_content = models.TextField(verbose_name="操作说明", null=True, blank=True, help_text="操作说明")
    operation_ip = models.CharField(max_length=32, verbose_name="请求ip地址", null=True, blank=True, help_text="请求ip地址")

    operation_time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = 'APi访问日志'
        verbose_name_plural = verbose_name
        ordering = ('-operation_time',)


class OrmOperationLog(models.Model):
    ADD = "add"
    MODIFY = "modify"
    EXEC = "exec"
    DELETE = "delete"

    OPERATE_TYPE_CHOICES = ((ADD, "新增"), (MODIFY, "修改"), (EXEC, "执行"), (DELETE, "删除"))

    operate_user = models.ForeignKey('account.UsersModel', on_delete=models.CASCADE, verbose_name='操作用户',
                                     related_name='ormop_user', null=True, blank=True)
    operate_type = models.CharField("操作类型", choices=OPERATE_TYPE_CHOICES, max_length=128)
    operate_obj = models.CharField("操作对象", max_length=64, default="")
    operate_summary = models.TextField("操作概要", max_length=500, default="")
    operate_detail = models.TextField("操作详情", default=[])
    created_time = models.DateTimeField("操作时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "ORM操作日志"
        verbose_name_plural = verbose_name
