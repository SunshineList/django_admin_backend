from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from imagekit.models import ProcessedImageField

from common.models import BaseModel


class ImageCaptcha(models.Model):
    uuid = models.UUIDField('uuid4', primary_key=True)
    captcha = models.CharField('图片验证码值', max_length=10)
    is_active = models.BooleanField('可用', default=False)
    expire_time = models.DateTimeField('验证码过期时间', db_index=True)

    class Meta:
        verbose_name = "管理后台登录验证图片"
        verbose_name_plural = verbose_name


class UsersModel(AbstractUser, BaseModel):
    ADMIN = "ADMIN"
    USER = "USER"

    USER_TYPE = ((ADMIN, "管理员"), (USER, "普通用户"))

    MALE = "1"
    FEMALE = "2"
    UNKNOW = "0"

    GENDER = ((MALE, "男"), (FEMALE, "女"), (UNKNOW, "未知"))

    mobile = models.CharField("手机号", max_length=10, unique=True)
    user_type = models.CharField("用户类型", max_length=10, choices=USER_TYPE, default=USER)
    gender = models.CharField("性别", max_length=5, choices="", default=UNKNOW)
    avatar = ProcessedImageField(help_text="压缩图片",
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

    @property
    def name(self) -> str:
        return self.first_name or self.username
