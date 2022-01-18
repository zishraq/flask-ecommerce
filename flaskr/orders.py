import uuid
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('orders', __name__, url_prefix='/orders')


@bp.route('/create-order', methods=['POST'])
@login_required
def create_shopping_cart():
    response = {
        'isSuccess': False,
        'message': 'Create an Order'
    }

    cart_ids = request.get_json()['cart_ids']

    order_id = str(uuid.uuid4())
    date_created = datetime.now()
    order_final = 0

    db = get_db()

    for cart_id in cart_ids:
        check_shopping_cart = db.execute(
            'SELECT * FROM shopping_cart '
            'WHERE cart_id = ? '
            'LIMIT 1',
            (cart_id,)
        ).fetchall()

        if len(check_shopping_cart) == 0:
            response['error'] = f'No such product with the id = {cart_id}'
            return response

        try:
            db.execute(
                f'INSERT INTO orders(order_id, cart_id, date_created, order_final) VALUES (?, ?, ?, ?)',
                (
                    order_id,
                    cart_id,
                    date_created,
                    order_final
                )
            )
            db.commit()
        except db.IntegrityError:
            response['error'] = f'{order_id} already exists.'
            return response

    response['isSuccess'] = True
    response['order_id'] = order_id
    return response


@bp.route('/add-to-order/<cart_id>/', methods=['PUT'])
@login_required
def add_to_cart(cart_id):
    response = {
        'isSuccess': False,
        'operation': 'Add to shopping cart'
    }

    product_name = request.get_json()['product_name']
    quantity = request.get_json()['quantity']

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

    return response


@bp.route('/get-all-carts', methods=['GET'])
def get_all_carts():
    db = get_db()
    carts = db.execute(
        'SELECT *'
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
