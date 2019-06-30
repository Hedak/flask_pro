from info import constants, db
from info.models import Category, News
from info.modules.profile import profile_blue
from flask import render_template, g, redirect, request, jsonify, current_app

from info.utils.captcha.response_code import RET
from info.utils.common import user_login_data
from info.utils.image_storage import storage


@profile_blue.route("/info")
@user_login_data
def user_info():
    """个人中心"""
    user = g.user
    # 表示没有登录，重定向到首页
    if not user:
        return redirect("/")
    data = {
        "user": user.to_dict()
    }
    return render_template("news/user.html", data=data)


@profile_blue.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    """修改个人资料"""
    # 不同的请求方式做不同的事情
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user.to_dict()})

    # 代表用户修改数据
    # 1.取到传入的参数
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    # 校验参数
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if gender not in ("MAN", "WOMAN"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    user.nick_name = nick_name
    user.gender = gender
    user.signature = signature

    return jsonify(errno=RET.OK, errmsg="ok")


@profile_blue.route("/pic_info", methods=["POST", "GET"])
@user_login_data
def pic_info():
    """修改头像"""
    user = g.user
    if request.method == "GET":
        return render_template("news/user_pic_info.html", data={"user": g.user.to_dict()})

    # 如果是post表示要修改图像
    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2 .上传头像
    try:
        # 使用自己封装的storage方法进行图片上传
        key = storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="头像上传失败")

    # 3.保存头像地址
    user.avatar_url = key
    return jsonify(errno=RET.OK, errmsg="ok", data={"avatar_url": constants.QINIU_DOMIN_PREFIX + key})


@profile_blue.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template("news/user_pass_info.html", data={"user": g.user.to_dict()})

    # 如果是post方式请求，则表示修改密码
    oid_password = request.json.get("old_password")
    new_password = request.json.get("new_password")
    # new_password2 = request.json.get("new_password2")

    # 2校验参数
    if not all([oid_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3判断旧密码是否正确
    user = g.user
    if not user.check_password(oid_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码输入错误")

    # 设置新密码
    user.password = new_password

    return jsonify(errno=RET.OK, errmsg="密码保存成功")


@profile_blue.route("/collection")
@user_login_data
def user_collection():
    """用户收藏新闻"""

    # 1获取参数
    page = request.args.get("p", 1)

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询用户指定页数收藏的新闻
    user = g.user

    new_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        new_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    new_dict_list = []
    for news in new_list:
        new_dict_list.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": new_dict_list
    }

    return render_template("news/user_collection.html", data=data)


@profile_blue.route("/news_release", methods=["GET", "POST"])
@user_login_data
def news_release():
    """新闻发布的页面"""
    if request.method == "GET":
        # 加载新闻分类数据
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        category_dict_list = []
        for category in categories:
            category_dict_list.append(category.to_dict())

        # 移除分类“最新”
        category_dict_list.pop(0)
        return render_template("news/user_news_release.html", data={"categories": category_dict_list})

    # 1.获取要提交的数据
    # 标题
    title = request.form.get("title")

    # 新闻来源
    source = "个人发布"

    # 摘要
    digest = request.form.get("digest")

    # 新闻内容
    content = request.form.get("content")

    # 索引图片
    index_image = request.files.get("index_image")

    # 分类id
    category_id = request.form.get("category_id")

    # 校验参数
    # 2.1 判断数据是否有值
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 3取到图片，将图片传到七牛云上
    try:
        index_image_data = index_image.read()
        key = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = g.user.id
    # 1代表审核状态
    news.status = 1
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg="数据保存失败")

    return jsonify(error=RET.OK, errmsg="ok")


@profile_blue.route("/news_list")
@user_login_data
def user_news_list():
    """用户发布新闻"""
    page = request.form.get("p", 1)

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger(e)
        page = 1

    user = g.user
    news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())

    data = {
        "news_list": news_dict_list,
        "total_page": total_page,
        "current_page": current_page,
    }

    return render_template("news/user_news_list.html", data=data)


@profile_blue.route("/user_follow")
@user_login_data
def user_follow():
    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 取到当前登录用户
    user = g.user

    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 获取当前页数据
        follows = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # TODO 暂时没有在个人中心关注列表中实现取消关注，在follow.js中实现，代码参考news/view.py/follow_user函数

    user_dict_li = []

    for follow_user in follows:
        user_dict_li.append(follow_user.to_dict())

    data = {
        "users": user_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return render_template('news/user_follow.html', data=data)
