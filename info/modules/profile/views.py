from info.modules.profile import profile_blue
from flask import render_template, g, redirect, request, jsonify

from info.utils.captcha.response_code import RET
from info.utils.common import user_login_data


@profile_blue.route("/info")
@user_login_data
def user_info():
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
