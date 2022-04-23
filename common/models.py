from django.db import models

# Create your models here.


class UploadFileName(models.Model):
    uuid_name = models.CharField('uuid_name', max_length=255, unique=True)
    name = models.CharField('原文件名字', max_length=255)
    url = models.CharField("文件路径", max_length=30)

    class Meta:
        verbose_name = '记录上传文件'
        verbose_name_plural = verbose_name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.uuid_name = self.uuid_name.split(".")[0]
        super(UploadFileName, self).save(force_insert, force_update, using, update_fields)
