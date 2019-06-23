from datetime import datetime
import random
import re
from wsgiref import headers

from flask import request, abort, current_app, make_response, jsonify, session

from info import redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.captcha.response_code import RET

from . import passport_blu


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
        redis_store.set("ImageCode_" + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    # 返回验证码图片
    response = make_response(image)

    response.headers["Content-Type"] = 'image/jpg'
    return response


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
        real_image_code = redis_store.get("ImageCode_" + image_code_id)
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
    result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 5], "1")
    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")
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

    mobile = params_dict.get("mobile")
    password = params_dict.get("password")
    smscode = params_dict.get("smscode")

    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    if not re.match("1[35678]\\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机格式不正确")
    # TODO:处理密码
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

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    return jsonify(errno=RET.OK, errmsg="注册成功")
