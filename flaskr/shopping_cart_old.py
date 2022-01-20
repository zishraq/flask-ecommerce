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

    try:
        db.execute(
            f'INSERT INTO shopping_cart_info(cart_id, username, created_at) VALUES (?, ?, ?)',
            (
                cart_id,
                username,
                created_at
            )
        )
        db.commit()

    except db.IntegrityError:
        response['error'] = f'Product with id "{cart_id}" already exists.'
        return response

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
                f'INSERT INTO products_by_cart(cart_id, product_id, quantity, added_at) VALUES (?, ?, ?, ?)',
                (
                    cart_id,
                    product['product_id'],
                    product['quantity'],
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
        'SELECT distinct cart_id FROM shopping_cart_info '
        'WHERE cart_id = ?',
        (cart_id,)
    ).fetchall()

    if len(check_cart) == 0:
        response['error'] = f'No such cart with the id = {cart_id}'
        return response

    username = g.user['username']

    if check_cart[0]['username'] != username:
        response['error'] = 'Unauthorized'
        return response

    added_products = request.get_json()['products']
    updated_at = datetime.now()

    for product in added_products:
        check_product = db.execute(
            'SELECT * FROM products '
            'WHERE product_id = ? '
            'LIMIT 1',
            (product['product_id'],)
        ).fetchall()

        if len(check_product) == 0:
            response['error'] = f'No such product with the id = {product["product_id"]}'
            return response

        previous_status = db.execute(
            'SELECT * FROM products_by_cart '
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
                f'INSERT INTO products_by_cart(cart_id, product_id, quantity, added_at) VALUES (?, ?, ?, ?)',
                (
                    cart_id,
                    product['product_id'],
                    product['quantity'],
                    updated_at
                )
            )
            db.commit()
        except db.IntegrityError:
            db.execute(
                'UPDATE products_by_cart SET quantity = ?, updated_at = ? '
                'WHERE cart_id = ? AND product_id = ?',
                (product['quantity'], updated_at, cart_id, product['product_id'])
            )
            db.commit()

    db.execute(
        'UPDATE shopping_cart_info SET updated_at = ? '
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
    username = g.user['username']

    carts = db.execute(
        'SELECT DISTINCT cart_id, created_at, updated_at '
        'FROM shopping_cart_info '
        'WHERE username = ? '
        'ORDER BY created_at ASC',
        (username,)
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
        'SELECT ps.product_id, p.product_name, ps.quantity, si.username, si.created_at, si.updated_at, SUM(p.price * ps.quantity) AS product_total_price '
        'FROM products_by_cart AS ps '
        'JOIN products AS p '
        'ON ps.product_id = p.product_id '
        'JOIN shopping_cart_info AS si '
        'ON si.cart_id = ps.cart_id '
        'WHERE ps.cart_id = ? '
        'GROUP BY ps.product_id '
        'ORDER BY si.created_at ASC ',
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

    for i in products:
        formatted_data = dict(i)

        if not username:
            username = formatted_data['username']

        if not created_at:
            created_at = formatted_data['created_at']

        if not updated_at:
            updated_at = formatted_data['updated_at']

        formatted_data.pop('username')
        formatted_data.pop('created_at')
        formatted_data.pop('updated_at')
        formatted_data['product_total_price'] = round(formatted_data['product_total_price'], 2)
        total_price += formatted_data['product_total_price']
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

    check_order_status = db.execute(
        'SELECT order_confirm FROM orders '
        'WHERE cart_id = ? '
        'LIMIT 1',
        (cart_id,)
    ).fetchall()

    if check_order_status[0]['order_confirm'] == 1:
        response['error'] = 'Cart already confirmed'
        return response

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

    check_order_status = db.execute(
        'SELECT order_confirm FROM orders '
        'WHERE cart_id = ?'
        'LIMIT 1',
        (cart_id,)
    ).fetchall()

    if check_order_status[0]['order_confirm'] == 1:
        response['error'] = 'Cart already confirmed'
        return response

    db.execute(
        'DELETE FROM shopping_cart '
        'WHERE cart_id = ? AND product_id = ?',
        (cart_id, product_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response
