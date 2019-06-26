from flask import render_template, current_app, request, jsonify, g
from info.models import User, News, Category
from info.utils.captcha.response_code import RET
from info.utils.common import user_login_data
from . import inex_blu


@inex_blu.route("/news_list")
def news_list():
    """获取首页新闻数据"""
    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "10")
    try:
        page = int(page)
        cid = int(cid)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    filters = []
    if cid != 1:
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    news_model_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_dict_list = []
    for news in news_model_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_dict_list": news_dict_list
    }
    return jsonify(errno=RET.OK, errmsg="ok", data=data)


# 首页
@inex_blu.route('/')
@user_login_data
def index():
    # user_id = session.get("user_id", None)
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)
    user = g.user
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

    categories = Category.query.all()

    category_list = []
    for category in categories:
        category_list.append(category.to_dict())
    data = {
        "user": user.to_dict() if user else None,
        "news_dict_list": news_dict_list,
        "category_list": category_list
    }

    return render_template("news/index.html", data=data)


# 显示网页的小图标
@inex_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
