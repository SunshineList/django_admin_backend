from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from imagekit.models import ProcessedImageField


class UsersModel(models.Model, AbstractUser):
    ADMIN = "ADMIN"
    USER = "USER"

    USER_TYPE = (
        (ADMIN, "管理员"),
        (USER, "普通用户"),
    )

    mobile = models.CharField("手机号", max_length=10, unique=True)
    user_type = models.CharField("用户类型", max_length=10, choices=USER_TYPE, default=USER)

    avatar = ProcessedImageField(
        help_text="压缩图片",
        upload_to='avatar/%Y/%m/%d',
        verbose_name=u'头像',
        null=True,
        blank=True,
        format='JPEG',
        options={'quality': settings.IMAGE_QUANLITY})

    is_active = models.BooleanField("账号是否生效", default=True)

    class Meta:
        db_table = 'users'
        verbose_name = '账号管理'
        verbose_name_plural = '账号管理'

    def __str__(self) -> str:
        return self.first_name or self.username
