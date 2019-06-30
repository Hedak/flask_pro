import time
from datetime import datetime, timedelta

from flask import current_app, g, jsonify, abort
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info import constants
from info.models import User, News, Category
from info.modules.admin import admin_blu
from info.utils.captcha.response_code import RET
from info.utils.common import user_login_data


@admin_blu.route('/index')
@user_login_data
def index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())


@admin_blu.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # 判断当前是否有登录，如果有登录直接重定向到管理员后台主页
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            return redirect(url_for('admin.index'))

        return render_template('admin/login.html')

    # 取到登录的参数
    username = request.form.get("username")
    password = request.form.get("password")

    # 判断参数
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数错误")

    # 查询当前用户
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="用户信息查询失败")

    if not user:
        return render_template('admin/login.html', errmsg="未查询到用户信息")

    # 校验密码
    if not user.check_password(password):
        return render_template('admin/login.html', errmsg="用户名或者密码错误")

    # 保存用户的登录信息
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name
    session["is_admin"] = user.is_admin

    # 跳转到后面管理首页
    return redirect(url_for('admin.index'))


@admin_blu.route("/user_count")
def user_count():
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新增人数
    mon_count = 0
    t = time.localtime()
    # begin_mon_date = datetime.strptime(('%d-%02d-01' % (t.tm_year, t.tm_mon)), "%Y-%m-%d")
    begin_mon_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 将字符串转成datetime对象
    begin_mon_date = datetime.strptime(begin_mon_date_str, "%Y-%m-%d")
    try:

        mon_count = User.query.filter(User.is_admin == False, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日增数
    day_count = 0
    begin_day_data = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_data).count()
    except Exception as e:
        current_app.logger.error(e)

    # 折线图数据
    active_time = []
    active_count = []

    # 取到今天的时间字符串
    today_date_str = ('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday))
    # 转成事件对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)
        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))
        count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                  User.last_login < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime('%Y-%m-%d'))

    # User.query.filter(User.is_admin == False, User.last_login >= 今天0点0分, User.last_login < 今天24点).count()
    # 反转，让最近的一天显示在最后
    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template("admin/user_count.html", data=data)


@admin_blu.route("/user_list")
def user_list():
    """管理员界面用户人数展示"""
    page = request.args.get("page", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    users = []
    current_page = 1
    total_page = 1

    try:
        paginate = User.query.filter(User.is_admin == False).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

        # 进行模型列表转字典列表
    user_dict_list = []
    for user in users:
        user_dict_list.append(user.to_admin_dict())

    data = {
        "users": user_dict_list,
        "total_page": total_page,
        "current_page": current_page,
    }

    return render_template('admin/user_list.html', data=data)


@admin_blu.route("/news_review")
def news_review():
    """新闻审核页面展示"""
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", None)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status != 0]
    if keywords:
        # 如果关键字存在，那么就添加关键字搜索
        filters.append(News.title.contains(keywords))

    try:
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    new_dict_list = []
    for news in news_list:
        new_dict_list.append(news.to_review_dict())

    context = {
        "current_page": current_page,
        "total_page": total_page,
        "news_list": new_dict_list

    }
    return render_template("admin/news_review.html", data=context)


@admin_blu.route("/news_review_detail/<int:news_id>")
def news_review_detail(news_id):
    """新闻审核页面跳转"""
    # 通过id查新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return render_template("admin/news_review_detail.html", data={"errmsg": "未查询到此新闻"})

    # 返回数据
    data = {"news": news.to_dict()}
    return render_template("admin/news_review_detail.html", data=data)


@admin_blu.route("/news_review_action", methods=["POST"])
def news_review_action():
    """新闻审核"""
    # 1接收参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2. 参数校验
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询到指定的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "accept":
        # 代表接受
        news.status = 0
    else:
        # 代表拒绝
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
        news.status = -1
        news.reason = reason

    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route("/news_edit")
def news_edit():
    """新闻编辑"""

    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    page = 1
    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status == 0]
    # 如果关键字存在，那么就添加关键字搜索
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    context = {"total_page": total_page, "current_page": current_page, "news_list": news_dict_list}

    return render_template('admin/news_edit.html', data=context)


@admin_blu.route("/news_edit_detail")
def news_edit_detail():
    """新闻编辑详细信息展示"""
    # 查询点击的新闻的相关数据并传入到模板中
    news_id = request.args.get("news_id")

    if not news_id:
        abort(404)

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_edit_detail.html", errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_edit_detail.html", errmsg="数据查询错误")

    if not news:
        return render_template("admin/news_edit_detail.html", errmsg="新闻不存在")

    # 查询分类数据
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/news_edit_detail.html", errmsg="数据查询错误")

    category_dict_list = []
    for category in categories:
        # 取到分类的字典
        cate_dict = category.to_dict()
        # 判断当前遍历到的分类是否是当前新闻的分类，如果是，则添加is_selected为true
        if category.id == news.category_id:
            cate_dict["is_selected"] = True
        category_dict_list.append(cate_dict)
    category_dict_list.pop(0)

    data = {
        "news": news.to_dict(),
        "categories": category_dict_list
    }

    return render_template("admin/news_edit_detail.html", data=data)
