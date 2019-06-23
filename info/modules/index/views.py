from flask import render_template, current_app, session
from info import redis_store
from info.models import User, News
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
    # 右侧新闻排行的逻辑
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
    # 定义一个空的字典列表，里面装的就是字典
    news_dict_list = []
    # 遍历对象列表，将对象的字典添加到字典列表中
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())
    data = {
        "user": user.to_dict() if user else None,
        "news_dict_list": news_dict_list
    }

    return render_template("news/index.html", data=data)


# 显示网页的小图标
@inex_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
