import uuid
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('shopping_cart', __name__, url_prefix='/shopping-cart')


@bp.route('/create-shopping-cart', methods=["POST"])
@login_required
def create_shopping_cart():
    response = {
        'isSuccess': False,
        'message': 'Create a shopping cart'
    }

    cart_id = str(uuid.uuid4())
    username = g.user['username']

    added_products = request.get_json()['products']
    created_at = datetime.now()

    db = get_db()

    for product in added_products:
        check_product = db.execute(
            'SELECT * FROM products '
            'WHERE product_id = ? '
            'ORDER BY created_at ASC',
            (product['product_id'],)
        ).fetchall()

        if len(check_product) == 0:
            response['error'] = f'No such product with the id = {product["product_id"]}'
            return response

        product_info = dict(check_product[0])

        if product_info['in_stock'] < product['quantity']:
            response['error'] = f'Only {product_info["in_stock"]} items available of product id = {product["product_id"]}'
            return response

        try:
            db.execute(
                f'INSERT INTO shopping_cart(cart_id, product_id, quantity, username, created_at) VALUES (?, ?, ?, ?, ?)',
                (
                    cart_id,
                    product['product_id'],
                    product['quantity'],
                    username,
                    created_at
                )
            )
            db.commit()
        except db.IntegrityError:
            response['error'] = f'Product with id "{product["product_id"]}" already exists.'
            return response

    response['isSuccess'] = True
    response['cart_id'] = cart_id
    return response


@bp.route('/add-to-cart/<cart_id>', methods=["PUT"])
@login_required
def add_to_cart(cart_id):
    response = {
        'isSuccess': False,
        'operation': 'Add to shopping cart'
    }

    db = get_db()

    check_cart = db.execute(
        'SELECT distinct cart_id FROM shopping_cart '
        'WHERE cart_id = ?',
        (cart_id,)
    ).fetchall()

    if len(check_cart) == 0:
        response['error'] = f'No such cart with the id = {cart_id}'
        return response

    username = g.user['username']
    added_products = request.get_json()['products']
    updated_at = datetime.now()

    for product in added_products:
        check_product = db.execute(
            'SELECT * FROM products '
            'WHERE product_id = ? '
            'ORDER BY created_at ASC',
            (product['product_id'],)
        ).fetchall()

        if len(check_product) == 0:
            response['error'] = f'No such product with the id = {product["product_id"]}'
            return response

        previous_status = db.execute(
            'SELECT * FROM shopping_cart '
            'WHERE cart_id = ? AND product_id = ? ',
            (cart_id, product['product_id'],)
        ).fetchall()

        if len(previous_status) != 0:
            product['quantity'] += previous_status[0]['quantity']

        product_info = dict(check_product[0])

        if product_info['in_stock'] < product['quantity']:
            response['error'] = f'Only {product_info["in_stock"]} items available of product id = {product["product_id"]}'
            return response

        try:
            db.execute(
                f'INSERT INTO shopping_cart(cart_id, product_id, quantity, username, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                (
                    cart_id,
                    product['product_id'],
                    product['quantity'],
                    username,
                    updated_at,
                    updated_at
                )
            )
            db.commit()
        except db.IntegrityError:
            db.execute(
                'UPDATE shopping_cart SET quantity = ? '
                'WHERE cart_id = ? AND product_id = ?',
                (product['quantity'], cart_id, product['product_id'])
            )
            db.commit()

    db.execute(
        'UPDATE shopping_cart SET created_at = ? '
        'WHERE cart_id = ?',
        (updated_at, cart_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/get-all-carts', methods=['GET'])
@login_required
def get_all_carts():
    db = get_db()
    carts = db.execute(
        'SELECT DISTINCT cart_id, created_at, updated_at '
        'FROM shopping_cart '
        'ORDER BY created_at ASC'
    ).fetchall()

    results = []

    for i in carts:
        results.append(dict(i))

    return {
        'isSuccess': True,
        'posts': results
    }


@bp.route('/get-products-by-cart-id/<cart_id>', methods=['GET'])
@login_required
def get_products_by_cart_id(cart_id):
    response = {
        'isSuccess': False,
        'operation': 'Get products by cart id'
    }

    db = get_db()

    products = db.execute(
        'SELECT s.product_id, p.product_name, s.quantity, s.username, s.created_at, s.updated_at '
        'FROM shopping_cart AS s '
        'INNER JOIN products AS p '
        'ON s.product_id = p.product_id '
        'WHERE s.cart_id = ? '
        'ORDER BY s.created_at ASC',
        (cart_id,)
    ).fetchall()

    calculation = db.execute(
        'SELECT s.product_id, SUM(p.price * s.quantity) AS product_total_price '
        'FROM shopping_cart AS s '
        'INNER JOIN products AS p '
        'ON s.product_id = p.product_id '
        'WHERE s.cart_id = ? '
        'GROUP BY s.product_id',
        (cart_id,)
    ).fetchall()

    if len(products) == 0:
        response['error'] = 'No such cart found'
        return response

    results = []
    username = None
    created_at = None
    updated_at = None
    total_price = 0

    for i in range(len(products)):
        formatted_data = dict(products[i])
        if not username:
            username = formatted_data['username']

        if not created_at:
            created_at = formatted_data['created_at']

        if not updated_at:
            updated_at = formatted_data['updated_at']

        formatted_data.pop('username')
        formatted_data.pop('created_at')
        formatted_data.pop('updated_at')
        formatted_data['product_total_price'] = round(calculation[i]['product_total_price'], 2)
        total_price += calculation[i]['product_total_price']
        results.append(formatted_data)

    response['isSuccess'] = True
    response['cart_id'] = cart_id
    response['username'] = username
    response['created_at'] = created_at
    response['updated_at'] = updated_at
    response['total_price'] = round(total_price, 2)
    response['products'] = results
    return response


@bp.route('/delete-shopping-cart/<cart_id>', methods=["DELETE"])
@login_required
def delete_shopping_cart(cart_id):
    response = {
        'isSuccess': False,
        'message': 'Delete a shopping cart'
    }

    db = get_db()

    db.execute(
        'DELETE FROM shopping_cart '
        'WHERE cart_id = ?',
        (cart_id,)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/delete-from-shopping-cart/<cart_id>/<product_id>', methods=["DELETE"])
@login_required
def delete_from_shopping_cart(cart_id, product_id):
    response = {
        'isSuccess': False,
        'message': 'Delete shopping cart item'
    }

    db = get_db()

    db.execute(
        'DELETE FROM shopping_cart '
        'WHERE cart_id = ? AND product_id = ?',
        (cart_id, product_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response
