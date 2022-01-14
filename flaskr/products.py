from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

from flaskr.auth import login_required, authorize_add_product
from flaskr.db import get_db

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/add_product', methods=['POST'])
@login_required
@authorize_add_product
def add_product():
    response = {
        'isSuccess': False,
        'operation': 'Add product'
    }

    db = get_db()

    body = dict(request.get_json())
    creation_data = {}
    creation_data['created_at'] = datetime.now()
    creation_data['created_by'] = g.user['username']
    creation_data['total_sold'] = 0

    if "products" in body:
        for product in body['products']:
            product.update(creation_data)

            try:
                db.execute(
                    f'INSERT INTO products (product_name, description, product_category, price, discount, created_at, created_by, in_stock, total_sold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        product['product_name'],
                        product['description'],
                        product['product_category'],
                        product['price'],
                        product['discount'],
                        product['created_at'],
                        product['created_by'],
                        product['in_stock'],
                        product['total_sold']
                    ),
                )
                db.commit()
            except db.IntegrityError:
                response['message'] = f'Product {product["product_name"]} already exists.'
                pass

            product['created_at'] = str(product['created_at'])
        response['total_inserted_products'] = len(body['products'])
        response['inserted_products'] = body['products']

    else:
        body.update(creation_data)

        try:
            db.execute(
                f'INSERT INTO products (product_name, description, product_category, price, discount, created_at, created_by, in_stock, total_sold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    body['product_name'],
                    body['description'],
                    body['product_category'],
                    body['price'],
                    body['discount'],
                    body['created_at'],
                    body['created_by'],
                    body['in_stock'],
                    body['total_sold']
                ),
            )
            db.commit()
        except db.IntegrityError:
            response['error'] = f'Product {body["product_name"]} already exists.'
            return response

        body['created_at'] = str(body['created_at'])
        response['inserted_products'] = body

    response['isSuccess'] = True
    return response


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
        'total_products': len(results),
        'posts': results
    })
