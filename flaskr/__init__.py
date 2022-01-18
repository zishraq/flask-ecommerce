# import os
#
# from flask import Flask
# from flask.json import JSONEncoder
# from datetime import date
#
# import flaskr
#
#
# class CustomJSONEncoder(JSONEncoder):
#     def default(self, obj):
#         try:
#             if isinstance(obj, date):
#                 return obj.strftime('%Y-%m-%d %H:%M:%S.%f')
#             iterable = iter(obj)
#         except TypeError:
#             pass
#         else:
#             return list(iterable)
#         return JSONEncoder.default(self, obj)
#
#
# def create_app(test_config=None):
#     # create and configure the app
#     app = Flask(__name__, instance_relative_config=True)
#     app.config.from_mapping(
#         SECRET_KEY='dev',
#         DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
#     )
#
#     app.config['JSON_SORT_KEYS'] = False
#     app.json_encoder = CustomJSONEncoder
#
#     if test_config is None:
#         app.config.from_pyfile('config.py', silent=True)
#     else:
#         app.config.from_mapping(test_config)
#
#     try:
#         os.makedirs(app.instance_path)
#     except OSError:
#         pass
#
#     @app.route('/index')
#     def index():
#         return 'Welcome to our Online Shop!'
#
#     from flaskr import db
#     db.init_app(app)
#
#     from flaskr import auth
#     app.register_blueprint(auth.bp)
#
#     from flaskr import products
#     app.register_blueprint(products.bp)
#
#     from flaskr import shopping_cart
#     app.register_blueprint(shopping_cart.bp)
#
#     from flaskr import orders
#     app.register_blueprint(orders.bp)
#     app.add_url_rule('/', endpoint='index')
#
#     return app
#
#
# if __name__ == '__main__':
#     flaskr.create_app().run(debug=True)
