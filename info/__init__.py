import redis
from flask import Flask, g, render_template
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

from config import config
import logging
from logging.handlers import RotatingFileHandler

from redis import StrictRedis

db = SQLAlchemy()
redis_store = None  # type:StrictRedis


def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 配置日志，并传入配置名字，以便能获取到指定配置所对应的日志等级
    setup_log(config_name)
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 通过app初始化
    db.init_app(app)
    global redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT,
                                    decode_responses=True)
    # 开启当前项目csrf保护
    CSRFProtect(app)
    # 设置session保护指定位置
    Session(app)
    # 防止包之间互相调用出错，在使用的时候再调用
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, "index_class")

    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):
        user = g.user
        data = {"user": user.to_dict() if user else None}
        return render_template("news/404.html", data=data)

    #
    @app.after_request
    def after_request(response):
        # 生成随机的csrf_token值
        csrf_token = generate_csrf()
        # 设置一个cookie
        response.set_cookie("csrf_token", csrf_token)
        return response

    # 注册蓝图
    from info.modules.index import inex_blu
    app.register_blueprint(inex_blu)
    # 图片验证码
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    from info.modules.news import news_blu
    app.register_blueprint(news_blu)

    from info.modules.profile import profile_blue
    app.register_blueprint(profile_blue)

    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    return app
