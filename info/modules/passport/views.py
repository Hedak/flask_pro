from flask import request, abort, current_app

from info import redis_store, constants
from info.utils.captcha.captcha import captcha

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
    return image
