import os

from flask import Flask
from flask.json import JSONEncoder
from datetime import date

from flaskr import db, auth, products, orders, shopping_cart


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.strftime('%Y-%m-%d %H:%M:%S.%f')
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)

app.config['JSON_SORT_KEYS'] = False
app.json_encoder = CustomJSONEncoder


@app.route('/index')
def index():
    return 'Welcome to our Online Shop!'


@app.route('/init-db')
def initialize_database():
    db.init_db()
    return {
        'message': 'Database Initialized'
    }


db.init_app(app)
app.register_blueprint(auth.bp)
app.register_blueprint(products.bp)
app.register_blueprint(shopping_cart.bp)
app.register_blueprint(orders.bp)
app.add_url_rule('/', endpoint='index')


if __name__ == '__main__':
    app.run(debug=True)
