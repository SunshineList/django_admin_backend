import copy

from django.db import connections, transaction
from django.db.models import QuerySet, Expression, Value, When, Case
from django.db.models.functions import Cast

from operation_log.middlewares import current_user


def get_request_ip(request):
    """
    获取请求IP
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
        return ip
    ip = request.META.get('REMOTE_ADDR', '')
    return ip or 'unknown'


def get_verbose_name(queryset=None, view=None, model=None):
    """
    获取 操作对象的verbose_name
    :param queryset:
    :param view:
    :param model:
    :return:
    """
    try:
        if queryset and hasattr(queryset, 'model'):
            model = queryset.model
        elif view and hasattr(view.get_queryset(), 'model'):
            model = view.get_queryset().model
        elif view and hasattr(view.get_serializer(), 'Meta') and hasattr(view.get_serializer().Meta, 'model'):
            model = view.get_serializer().Meta.model
        if model:
            return getattr(model, '_meta').verbose_name
        else:
            model = queryset.model._meta.verbose_name
    except Exception as e:
        pass
    return model if model else ""


class MyQuerySet(QuerySet):

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False, is_log=False):
        super(MyQuerySet, self).bulk_create(objs, batch_size=None, ignore_conflicts=False)
        operate_user = current_user()
        if is_log:
            for obj in objs:
                # TODO 创建日志
                pass

    def bulk_update(self, objs, fields, batch_size=None, is_log=False, **kwargs):
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
                if is_log:
                    qs = self.filter(pk__in=pks)
                    old_objs = [copy.deepcopy(item) for item in qs]
                    kwargs["updated_by"] = kwargs.get("updated_by") or current_user()
                    qs.update(**update_kwargs)
                    operate_user = current_user()
                    for index, obj in enumerate(objs):
                        # TODO 批量更新日志
                        pass
                else:
                    self.filter(pk__in=pks).update(**update_kwargs)

    def update(self, is_log=False, **kwargs):
        old_objs = [copy.deepcopy(item) for item in self]
        kwargs["updated_by"] = kwargs.get("updated_by") or current_user()
        super().update(**kwargs)
        if is_log:
            operate_user = current_user()
            for index, obj in enumerate(self):
                # TODO 更新日志
                pass

    def create(self, is_log=False, **kwargs):
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, is_log=is_log)
        return obj

    def delete(self, is_log=False):
        old_objs = [copy.deepcopy(item) for item in self]
        count, obj_dict = super().delete()
        if is_log:
            operate_user = current_user()
            # TODO 删除日志
        return count, obj_dict
