import os
import sys


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_data_path(filename):
    return os.path.join(get_app_dir(), filename)


def resolve_asset_path(relative_path):
    if not relative_path:
        return ""
    if os.path.isabs(relative_path):
        return relative_path if os.path.exists(relative_path) else ""
    if getattr(sys, 'frozen', False):
        bundled = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundled):
            return bundled
    local = os.path.join(get_app_dir(), relative_path)
    return local if os.path.exists(local) else ""
