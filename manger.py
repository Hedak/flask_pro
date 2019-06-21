from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import app, db

# 设置项目运行参数
manger = Manager(app)
# 将app与db关联
Migrate(app, db)
# 将迁移命令添加到manger中
manger.add_command('db', MigrateCommand)


@app.route('/')
def index():
    return 'hello world'


if __name__ == '__main__':
    manger.run()
