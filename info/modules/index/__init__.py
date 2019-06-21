from flask import Blueprint

# 创建蓝图
inex_blu = Blueprint("index", __name__)

from . import views
