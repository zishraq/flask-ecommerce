import uuid
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('orders', __name__, url_prefix='/orders')


@bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
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
