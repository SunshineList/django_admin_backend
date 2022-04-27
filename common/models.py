import copy

from django.conf import settings
from django.db import models

# Create your models here.
from django.db.models import Model
from django.db import connections, transaction
from django.db.models import QuerySet, Expression, Value, When, Case
from django.db.models.functions import Cast
from operation_log.middlewares import current_user
from operation_log.models import OrmOperationLog


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


class OperationLogFunc:
    def __init__(self):
        self.ignore_module = (OrmOperationLog, )
        self.ignore_fields = ()

    @transaction.atomic
    def log_created(self, sender, **kwargs):
        if sender in self.ignore_module:
            return
        instance = kwargs.get("new_obj", None)
        operate_user = kwargs.get("operate_user", None)
        field_list = sender._meta.fields
        operate_detail = []
        for i in field_list[1:]:
            if i.name in self.ignore_fields:
                continue
            # help_text 这个属性 可以做为特殊的标记用途
            if i.help_text:
                continue
            if isinstance(getattr(instance, i.name), Model):
                operate_detail.append({
                    "name": i.verbose_name,
                    "value": getattr(instance, i.name).__str__()
                })
            else:
                operate_detail.append({"name": i.verbose_name, "value": getattr(instance, i.name)})
        OrmOperationLog.objects.create(
            operate_user=operate_user,
            operate_type=OrmOperationLog.ADD,
            operate_detail=operate_detail,
            operate_obj=instance._meta.verbose_name,
            operate_summary="新增" + instance._meta.verbose_name + "[" + str(instance) + "]",
        )

    @transaction.atomic
    def log_delete(self, sender, **kwargs):
        if sender in self.ignore_module:
            return
        instance = kwargs.get("delete_obj", None)
        operate_user = kwargs.get("operate_user", None)
        field_list = sender._meta.fields
        operate_detail = []
        for i in field_list[1:]:
            if i.name in self.ignore_fields:
                continue
            if i.help_text:
                continue
            if isinstance(getattr(instance, i.name), Model):
                operate_detail.append({
                    "name": i.verbose_name,
                    "value": getattr(instance, i.name).__str__()
                })
            else:
                operate_detail.append({"name": i.verbose_name, "value": getattr(instance, i.name)})
        OrmOperationLog.objects.create(
            operate_user=operate_user,
            operate_type=OrmOperationLog.DELETE,
            operate_detail=operate_detail,
            operate_obj=instance._meta.verbose_name,
            operate_summary="删除" + instance._meta.verbose_name + str(instance),
        )

    @transaction.atomic
    def log_update(self, sender, **kwargs):
        if sender in self.ignore_module:
            return
        new_obj = kwargs.get("new_obj", None)
        old_obj = kwargs.get("old_obj", None)
        operate_user = kwargs.get("operate_user", None)
        field_list = sender._meta.fields
        operate_detail = []
        for i in field_list[1:]:
            if i.name in self.ignore_fields:
                continue
            if i.help_text:
                continue
            new_value = getattr(new_obj, i.name)
            old_value = getattr(old_obj, i.name)
            if isinstance(new_value, Model) and isinstance(old_value, Model):
                if new_value.__str__() != old_value.__str__():
                    value = "[{}] ==> [{}]".format(old_value.__str__(), new_value.__str__())
                    operate_detail.append({"name": i.name, "value": value})
            else:
                if new_value != old_value:
                    value = "[{}] ==> [{}]".format(old_value, new_value)
                    operate_detail.append({"name": i.name, "value": value})
        if operate_detail:
            print(operate_detail)
            OrmOperationLog.objects.create(
                operate_user=operate_user,
                operate_type=OrmOperationLog.MODIFY,
                operate_detail=operate_detail,
                operate_obj=new_obj._meta.object_name,
                operate_summary="修改" + new_obj._meta.verbose_name + str(new_obj),
            )


class CustomQuerySet(QuerySet):
    def __init__(self):
        super(CustomQuerySet, self).__init__()
        self.is_log = getattr(settings, "OPEN_LOG_RECORD", False)

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        super(CustomQuerySet, self).bulk_create(objs, batch_size=None, ignore_conflicts=False)
        operate_user = current_user()
        if self.is_log:
            for obj in objs:
                OperationLogFunc().log_created(sender=type(obj),
                                               new_obj=obj,
                                               operate_user=operate_user)

    def bulk_update(self, objs, fields, batch_size=None, **kwargs):
        """
        Update the given fields in each of the given objects in the database.
        """
        if batch_size is not None and batch_size < 0:
            raise ValueError('Batch size must be a positive integer.')
        if not fields:
            raise ValueError('Field names must be given to bulk_update().')
        objs = tuple(objs)
        if any(obj.pk is None for obj in objs):
            raise ValueError('All bulk_update() objects must have a primary key set.')
        fields = [self.model._meta.get_field(name) for name in fields]
        if any(not f.concrete or f.many_to_many for f in fields):
            raise ValueError('bulk_update() can only be used with concrete fields.')
        if any(f.primary_key for f in fields):
            raise ValueError('bulk_update() cannot be used with primary key fields.')
        if not objs:
            return
        # PK is used twice in the resulting update query, once in the filter
        # and once in the WHEN. Each field will also have one CAST.
        max_batch_size = connections[self.db].ops.bulk_batch_size(['pk', 'pk'] + fields, objs)
        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
        requires_casting = connections[self.db].features.requires_casted_case_in_updates
        batches = (objs[i:i + batch_size] for i in range(0, len(objs), batch_size))
        updates = []
        for batch_objs in batches:
            update_kwargs = {}
            for field in fields:
                when_statements = []
                for obj in batch_objs:
                    attr = getattr(obj, field.attname)
                    if not isinstance(attr, Expression):
                        attr = Value(attr, output_field=field)
                    when_statements.append(When(pk=obj.pk, then=attr))
                case_statement = Case(*when_statements, output_field=field)
                if requires_casting:
                    case_statement = Cast(case_statement, output_field=field)
                update_kwargs[field.attname] = case_statement
            updates.append(([obj.pk for obj in batch_objs], update_kwargs))

        with transaction.atomic(using=self.db, savepoint=False):
            for pks, update_kwargs in updates:
                if self.is_log:
                    qs = self.filter(pk__in=pks)
                    old_objs = [copy.deepcopy(item) for item in qs]
                    kwargs["updated_by"] = kwargs.get("updated_by") or current_user()
                    qs.update(**update_kwargs)
                    operate_user = current_user()
                    for index, obj in enumerate(objs):
                        OperationLogFunc().log_update(sender=type(obj),
                                                      new_obj=obj,
                                                      operate_user=operate_user,
                                                      old_obj=old_objs[index])
                else:
                    self.filter(pk__in=pks).update(**update_kwargs)

    def update(self, **kwargs):
        old_objs = [copy.deepcopy(item) for item in self]
        kwargs["updated_by"] = kwargs.get("updated_by") or current_user()
        super().update(**kwargs)
        if self.is_log:
            operate_user = current_user()
            for index, obj in enumerate(self):
                OperationLogFunc().log_update(sender=type(obj),
                                              new_obj=obj,
                                              operate_user=operate_user,
                                              old_obj=old_objs[index])

    def delete(self):
        old_objs = [copy.deepcopy(item) for item in self]
        count, obj_dict = super().delete()
        if self.is_log:
            operate_user = current_user()
            for index, obj in enumerate(old_objs):
                OperationLogFunc().log_update(sender=type(obj),
                                              delete_obj=obj,
                                              operate_user=operate_user)
        return count, obj_dict


# 抽象一个model用于方便记录orm的操作日志记录
class BaseModel(models.Model):
    last_update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    operate_user = models.ForeignKey('account.UsersModel',
                                     on_delete=models.CASCADE,
                                     verbose_name='更新用户',
                                     related_name='ormupdate_user',
                                     null=True,
                                     blank=True)
    objects = CustomQuerySet().as_manager()

    class Meta:
        abstract = True

    is_log = getattr(settings, "OPEN_LOG_RECORD", False)

    def save(self, old_obj=None, *args, **kwargs):
        old_obj = copy.deepcopy(type(self)).objects.filter(id=self.id).first() if self.id else None
        operate_user = current_user()
        if old_obj:
            self.updated_by = operate_user
        else:
            self.created_by = operate_user
        super().save(*args, **kwargs)
        if self.is_log:
            if old_obj:
                OperationLogFunc().log_update(sender=type(self),
                                              new_obj=self,
                                              old_obj=old_obj,
                                              operate_user=operate_user)

            else:
                OperationLogFunc().log_created(sender=type(self),
                                               new_obj=self,
                                               operate_user=operate_user)

    def delete(self, using=None):
        super().delete(using)
        if self.is_log:
            operate_user = current_user()
            OperationLogFunc().log_delete(sender=type(self),
                                          delete_obj=self,
                                          operate_user=operate_user)
