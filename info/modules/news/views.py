from info import constants
from info.models import User, News
from info.modules.news import news_blu
from flask import render_template, session, current_app


@news_blu.route("/<int:news_id>")
def news_detail(news_id):
    """新闻详情"""
    user_id=session.get("user_id",None)
    user=None
    # 查询用户是否登录
    if user_id:
        try:
            user=User.query.get(user_id)
        except Exception as e:
            current_app.logger(e)
    news_list=[]
    try:news_list=News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger(e)
    news_dict_list=[]
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())





    data = {
        "user":user.to_dict() if user  else None,
        "news_dict_list":news_dict_list

    }
    return render_template("news/detail.html", data=data)
