from flask import render_template, current_app
from info import redis_store
from . import inex_blu


# 首页
@inex_blu.route('/')
def index():
    return render_template("news/index.html")


# 显示网页的小图标
@inex_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
