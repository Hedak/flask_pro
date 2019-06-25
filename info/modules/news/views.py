from info import constants
from info.models import User, News
from info.modules.news import news_blu
from flask import render_template, session, current_app, g

from info.utils.common import user_login_data


@news_blu.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    """新闻详情"""
    #
    # user_id = session.get("user_id", None)
    # user = None
    # if user_id:
    #     # 查询用户的模型
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger(e)

    # 查询用户登录信息
    user = g.user
    # 右侧新闻排行的逻辑实现
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger(e)

    # 定义一个空的字典列表，里面装的就是字典
    news_dict_list = []

    # 遍历对象列表，将对象的字典添加到字典列表中
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_list": news_dict_list

    }
    return render_template("news/detail.html", data=data)
