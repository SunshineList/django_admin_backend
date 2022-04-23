# coding=utf-8
from importlib import import_module
from os import path
import os, sys

import django
import six
from django.core.management.base import CommandError
from django.core.management.templates import TemplateCommand
from django.conf import settings

file_path = os.path.dirname(os.path.abspath("__file__"))


def import_string(dotted_path):
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as e:
        six.reraise(ImportError, ImportError(e), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        six.reraise(ImportError, ImportError(e), sys.exc_info()[2])


class NewTemplateCommand(TemplateCommand):
    def handle_template(self, template, subdir):
        if template is None:
            if not os.path.exists(path.join((file_path), "app_template")):
                # 如果没有文件夹不要报错使用默认的模板
                return path.join(django.__path__[0], 'conf', subdir)
            return path.join(file_path, "app_template")
        else:
            if template.startswith('file://'):
                template = template[7:]
            expanded_template = path.expanduser(template)
            expanded_template = path.normpath(expanded_template)
            if path.isdir(expanded_template):
                return expanded_template
            if self.is_url(template):
                # downloads the file and returns the path
                absolute_path = self.download(template)
            else:
                absolute_path = path.abspath(expanded_template)
            if path.exists(absolute_path):
                return self.extract(absolute_path)


class Command(NewTemplateCommand):
    def handle(self, *args, **options):
        # 做假数据欺骗Django command
        options = {
            "name": options["name"],  # sys.argv[1],
            "directory": None,
            "verbosity": 1,
            "extensions": ['py'],
            "files": [],
            "template": None,
            "traceback": False,
            "settings": None,
            "pythonpath": None
        }
        app_name, target = options.pop('name'), options.pop('directory')
        self.validate_name(app_name, "app")

        # Check that the app_name cannot be imported.
        try:
            import_module(app_name)
        except ImportError:
            pass
        else:
            raise CommandError("已有相同的app模块 无法创建")

        super(Command, self).handle('app', app_name, target, **options)

        if not settings.configured:
            settings.configure()
            django.setup()

        file = "%s" % os.sep.join([file_path, file_path.split("%s" % os.sep)[-1], "settings.py"])

        # 自动注册进settings 但是这块写入挺难受的
        self.alter(file=file,
                   new_str="'%s'" % (".".join([app_name, "apps", str(app_name).capitalize() + "Config"])).replace("-",
                                                                                                                  "") + ",\n")

    def alter(self, file, new_str=None):
        file_data = []
        if sys.version_info >= (3, 0):  # 兼容性问题
            with open(file, "r", encoding="utf-8") as f:
                for index, line in enumerate(f):
                    file_data.append(line)
                    if "INSTALLED_APPS" in line:
                        file_data.insert(index + 1, "    " + new_str)
                        break
            with open(file, "w", encoding="utf-8") as f:
                f.write("".join(file_data))
        else:
            with open(file, "r") as f:
                for index, line in enumerate(f):
                    file_data.append(line)
                    if "INSTALLED_APPS" in line:
                        file_data.insert(index + 1, "    " + new_str)
                        break
            with open(file, "w") as f:
                f.write("".join(file_data))


if __name__ == "__main__":
    # 兼容两种运行方法 1. python startapp.py 模块名称    2. python startapp.py 手动输入模块名
    try:
        app_name = sys.argv[1]
    except IndexError:
        app_name = sys.version_info < (3, 0) and raw_input("输入app模块名: ") or input(
            "输入app模块名: ")  # 兼容Python2 和 Python3的输入
        if not app_name:
            raise CommandError("无效模块名称")

    Command().handle(name=app_name)
