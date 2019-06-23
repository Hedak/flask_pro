from flask import render_template, current_app, session
from info import redis_store
from info.models import User
from . import inex_blu


# 首页
@inex_blu.route('/')
def index():
    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
    data = {
                "user": user.to_dict() if user else None
            }

    return render_template("news/index.html", data=data)


# 显示网页的小图标
@inex_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
