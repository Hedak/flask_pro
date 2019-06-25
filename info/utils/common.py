# 共用的自定义工具
import functools

from flask import session, current_app, g

from info.models import User


def do_index_class(index):
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    return ""


# 定义装饰器来判断用户是否是登陆状态
def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # 取到用户id
        user_id = session.get("user_id", None)
        user = None
        if user_id:
            # 尝试查询用户模型
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        # 把查询粗来的值赋给g变量
        g.user = user
        return f(*args, **kwargs)

    return wrapper
