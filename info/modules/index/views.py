from flask import render_template
from info import redis_store
from . import inex_blu


@inex_blu.route('/')
def index():
    return render_template("news/index.html")
