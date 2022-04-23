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
    status = models.BooleanField(default=False, verbose_name="响应状态", help_text="响应状态")

    operation_time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ('-operation_time',)
