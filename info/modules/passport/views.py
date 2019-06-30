from datetime import datetime
import random
import re

from flask import request, abort, current_app, make_response, jsonify, session

from info import redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.captcha.response_code import RET

from . import passport_blu


# 生成图片验证码
@passport_blu.route("/image_code")
def get_image_code():
    """生成图片验证码并返回"""

    # 取到参数
    # args:取到url中问好后面的参数
    image_code_id = request.args.get("imageCodeId", None)
    # 判断是否有值
    if not image_code_id:
        return abort(403)
    name, text, image = captcha.generate_captcha()

    try:
        redis_store.set("ImageCodeId_" + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    # 返回验证码图片
    response = make_response(image)

    response.headers["Content-Type"] = 'image/jpg'
    return response


# 生成手机验证码
@passport_blu.route('/sms_code', methods=["POST"])
def send_sms_code():
    """生成手机验证码并返回"""

    params_dict = request.json
    # 获取电话号码
    mobile = params_dict.get("mobile")
    # 获取输入的图片验证码
    image_code = params_dict.get("image_code")
    # 获取产生的图片验证码随机值
    image_code_id = params_dict.get("image_code_id")

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    # 校验手机号码
    if not re.match("1[35678]\\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式不正确")
    try:
        # 根据image_code_id从数据库中取出真实的图片验证码内容
        real_image_code = redis_store.get("ImageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")
    # 与用户输入的图片验证码进行比对，如果结果不一致，返回验证码错误信息
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")
    # 如果校验通过，设置短信验证码，共六位，位数不够在前面补上零
    sms_code_str = "%06d" % random.randint(0, 999999)
    current_app.logger.debug("短信验证码内容是: %s" % sms_code_str)
    # 发送短信验证码
    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 5], "1")
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")
    try:
        # 将短息验证码内容保存到数据库
        redis_store.set("SMS_" + mobile, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 告知发送结果
    return jsonify(errno=RET.OK, errmsg="发送成功")


# 注册
@passport_blu.route("/register", methods=["POST"])
def register():
    params_dict = request.json
    # 获取手机号码，密码，图片验证码
    mobile = params_dict.get("mobile")
    password = params_dict.get("password")
    smscode = params_dict.get("smscode")

    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    if not re.match("1[35678]\\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机格式不正确")

    try:
        real_sms_code = redis_store.get("SMS_" + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据查询错误")
    if not real_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg="验证码已过期")
    if real_sms_code != smscode:
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    user = User()
    # 初始化模型
    user.mobile = mobile
    user.nick_name = mobile
    user.last_login = datetime.now()
    user.password = password

    try:
        # 将数据存到数据库
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")
    # 设置session值
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    return jsonify(errno=RET.OK, errmsg="注册成功")


# 登录
@passport_blu.route("/login", methods=["POST"])
def login():
    # 获取数据
    params_dict = request.json
    mobile = params_dict.get("mobile")
    passport = params_dict.get("passport")

    if not all([mobile, passport]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if not re.match("1[35678]\\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式不正确")

    try:
        # 根据电话号码查询用户
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")
    if not user.check_password(passport):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或者密码输入错误")
    # 设置session
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name
    # 设置最后登录为登录时的当前时间
    user.last_login = datetime.now()

    return jsonify(errno=RET.OK, errmsg="登陆成功")


# 退出登录
@passport_blu.route("/logout")
def logout():
    # 删除session值，返回主页，为未登录的状态
    session.pop("user_id", None)
    session.pop("mobile", None)
    session.pop("nick_name", None)
    # 要清除is_admin的值，如果不清除，先登录管理员，会保存到session，再登录普通用户，又能访问管理员页面
    session.pop("is_admin", None)

    return jsonify(errno=RET.OK, errmsg="退出成功")
