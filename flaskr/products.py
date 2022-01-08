from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('products', __name__)


@bp.route('/add_product', methods=['POST'])
def add_product():
    # print(dir(request))
    print(request.authorization)
    print(request)
    body = dict(request.get_json())
    body['created_at'] = datetime.now()
    body['updated_at'] = datetime.now()
    body['total_sold'] = 0

    db = get_db()

    try:
        db.execute(
            f'INSERT INTO products (product_name, description, product_category, price, discount, created_at, updated_at, in_stock, total_sold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                body['product_name'],
                body['description'],
                body['product_category'],
                body['price'],
                body['discount'],
                body['created_at'],
                body['updated_at'],
                body['in_stock'],
                body['total_sold']
            ),
        )
        db.commit()
    except db.IntegrityError:
        error = f'User {body["product_name"]} is already exists.'
    else:
        # return redirect(url_for("auth.login"))
        return {
            'isSuccess': True,
            'message': 'Successfully entered'
        }


@bp.route('/all-products', methods=['GET'])
def all_products():
    db = get_db()
    products = db.execute(
        'SELECT * FROM products ORDER BY created_at DESC'
    ).fetchall()

    results = []

    for i in products:
        results.append(dict(i))

    return jsonify({
        'isSuccess': True,
        'posts': results
    })
