from info import constants
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