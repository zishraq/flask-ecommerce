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

    products = request.get_json()['products']
    created_at = datetime.now()

    db = get_db()

    for product in products:
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
            response['error'] = f'{cart_id} already exists.'
            return response

    response['isSuccess'] = True
    response['cart_id'] = cart_id
    return response


@bp.route('/add-to-cart/<cart_id>', methods=['PUT'])
@login_required
def add_to_cart(cart_id):
    response = {
        'isSuccess': False,
        'operation': 'Add to shopping cart'
    }

    product_name = request.get_json()['product_name']
    quantity = request.get_json()['quantity']
    username = g.user['username']

    if not product_name:
        response['error'] = 'Product name is required.'
        return response

    else:
        db = get_db()
        db.execute(
            'UPDATE shopping_cart SET product_name = ?, quantity = ?'
            ' WHERE cart_id = ?',
            (product_name, quantity, cart_id)
        )
        db.commit()
        response['isSuccess'] = True

    db = get_db()

    try:
        db.execute(
            f'INSERT INTO shopping_cart(cart_id, username) VALUES (?, ?)',
            (
                cart_id,
                username
            )
        )
        db.commit()
    except db.IntegrityError:
        response['error'] = f'{cart_id} already exists.'
        return response
    else:
        response['isSuccess'] = True
        response['cart_id'] = cart_id

    return response


@bp.route('/get-all-carts', methods=['GET'])
def get_all_carts():
    db = get_db()
    carts = db.execute(
        'SELECT DISTINCT cart_id'
        ' FROM shopping_cart'
        ' ORDER BY created_at ASC'
    ).fetchall()

    results = []

    for i in carts:
        results.append(dict(i))

    return {
        'isSuccess': True,
        'posts': results
    }


@bp.route('/get-products-by-cart-id/<cart_id>', methods=['GET'])
def get_products_by_cart_id(cart_id):
    response = {
        'isSuccess': False,
        'operation': 'Get products by cart id'
    }

    db = get_db()

    products = db.execute(
        'SELECT s.product_id, p.product_name, s.quantity, s.username, s.created_at FROM shopping_cart AS s '
        'JOIN products AS p '
        'ON s.product_id = p.product_id '
        'WHERE s.cart_id = ?'
        'ORDER BY s.created_at ASC',
        (cart_id,)
    ).fetchall()

    if not len(products):
        response['error'] = 'No such cart found'
        return response

    results = []
    username = None
    created_at = None

    for i in products:
        formatted_data = dict(i)
        if not username:
            username = formatted_data['username']

        if not created_at:
            username = formatted_data['created_at']

        formatted_data.pop('username')
        formatted_data.pop('created_at')
        results.append(formatted_data)

    response['isSuccess'] = True
    response['cart_id'] = cart_id
    response['username'] = username
    response['created_at'] = created_at
    response['products'] = results
    return response
