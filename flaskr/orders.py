import uuid
from datetime import datetime

from flask import Blueprint, g, request

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
    created_at = datetime.now()
    is_confirmed = 0

    db = get_db()

    try:
        db.execute(
            f'INSERT INTO order_info(order_id, created_at, is_confirmed) VALUES (?, ?, ?)',
            (
                order_id,
                created_at,
                is_confirmed
            )
        )
        db.commit()

    except db.IntegrityError:
        response['error'] = f'Order id "{order_id}" already exists.'
        return response

    for cart_id in cart_ids:
        check_shopping_cart = db.execute(
            'SELECT * FROM shopping_cart_info '
            'WHERE cart_id = ? '
            'LIMIT 1',
            (cart_id,)
        ).fetchall()

        if len(check_shopping_cart) == 0:
            response['error'] = f'No such cart with the id = {cart_id}'
            return response

        check_cart_in_order = db.execute(
            'SELECT DISTINCT order_id, cart_id '
            'FROM carts_by_orders '
            'WHERE cart_id = ? ',
            (cart_id,)
        ).fetchall()

        if len(check_cart_in_order) != 0:
            response['error'] = f'Cart already exists in order_id = {check_cart_in_order[0]["order_id"]}. You can remove from that order'
            return response

        try:
            db.execute(
                f'INSERT INTO carts_by_orders(order_id, cart_id, added_at) VALUES (?, ?, ?)',
                (
                    order_id,
                    cart_id,
                    created_at
                )
            )
            db.commit()
        except db.IntegrityError:
            response['error'] = f'{order_id} already exists.'
            return response

    response['isSuccess'] = True
    response['order_id'] = order_id
    return response


@bp.route('/add-to-order/<order_id>', methods=["PUT"])
@login_required
def add_to_order(order_id):
    response = {
        'isSuccess': False,
        'operation': 'Add to Order'
    }

    db = get_db()

    check_cart = db.execute(
        'SELECT distinct order_id FROM order_info '
        'WHERE order_id = ?',
        (order_id,)
    ).fetchall()

    if len(check_cart) == 0:
        response['error'] = f'No such order with the id = {order_id}'
        return response

    added_carts = request.get_json()['cart_ids']
    updated_at = datetime.now()

    for cart in added_carts:
        check_product = db.execute(
            'SELECT * FROM shopping_carts '
            'WHERE cart_id = ? '
            'LIMIT 1',
            (cart['cart_id'],)
        ).fetchall()

        if len(check_product) == 0:
            response['error'] = f'No such cart with the id = {cart["cart_id"]}'
            return response

        try:
            db.execute(
                f'INSERT INTO carts_by_orders(order_id, cart_id, added_at) VALUES (?, ?, , ?, ?, ?)',
                (
                    order_id,
                    cart['cart_id'],
                    updated_at
                )
            )
            db.commit()
        except db.IntegrityError:
            response['error'] = f'Cart {cart["cart_id"]} already exists.'
            return response

    db.execute(
        'UPDATE order_info SET updated_at = ? '
        'WHERE order_id = ?',
        (updated_at, order_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/confirm-order/<order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    response = {
        'isSuccess': False,
        'message': 'Confirm an Order'
    }

    db = get_db()

    check_order_status = db.execute(
        'SELECT is_confirmed FROM order_info '
        'WHERE order_id = ?'
        'LIMIT 1',
        (order_id,)
    ).fetchall()

    if len(check_order_status) == 0:
        response['error'] = f'No such order with the id = {order_id}'
        return response

    if check_order_status[0]['is_confirmed'] == 1:
        response['error'] = 'Order already confirmed'
        return response

    products = db.execute(
        'SELECT DISTINCT p.product_id, p.product_name, p.in_stock, SUM(ps.quantity) AS total_ordered '
        'FROM orders AS o '
        'JOIN products_by_cart AS ps '
        'ON o.cart_id = s.cart_id '
        'JOIN products AS p '
        'ON p.product_id = s.product_id '
        'GROUP BY p.product_id'
    ).fetchall()

    for i in products:
        formatted_data = dict(i)

        if formatted_data['in_stock'] < formatted_data['total_ordered']:

            response['error'] = f'Only {formatted_data["in_stock"]} items available of ' \
                                f'product id = {formatted_data["product_id"]}. ' \
                                f'You have ordered a total of {formatted_data["total_ordered"]} ' \
                                f'combining all the carts. You can update your carts. '
            return response

    for i in products:
        formatted_data = dict(i)
        update_in_stock = formatted_data['in_stock'] - formatted_data['quantity']

        db.execute(
            'UPDATE products SET in_stock = ?, total_sold = ? '
            'WHERE product_id = ?',
            (update_in_stock, formatted_data['quantity'], formatted_data['product_id'])
        )
        db.commit()

    db.execute(
        'UPDATE orders SET is_confirmed = 1 '
        'WHERE order_id = ?',
        (order_id,)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/get-all-orders', methods=['GET'])
@login_required
def get_all_orders():
    username = g.user['username']

    db = get_db()
    carts = db.execute(
        'SELECT DISTINCT oi.order_id, co.cart_id, oi.is_confirmed, oi.created_at, oi.updated_at '
        'FROM order_info AS oi '
        'JOIN carts_by_orders AS co '
        'ON co.order_id = oi.order_id '
        'JOIN shopping_cart_info AS si '
        'ON si.cart_id = co.cart_id '
        'WHERE si.username = ? '
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


@bp.route('/delete-order/<order_id>', methods=["DELETE"])
@login_required
def delete_shopping_cart(order_id):
    response = {
        'isSuccess': False,
        'message': 'Delete an order'
    }

    db = get_db()

    check_order_status = db.execute(
        'SELECT is_confirmed FROM orders '
        'WHERE order_id = ?'
        'LIMIT 1',
        (order_id,)
    ).fetchall()

    if len(check_order_status) == 0:
        response['error'] = f'No such order with the id = {order_id}'
        return response

    if check_order_status[0]['is_confirmed'] == 1:
        response['error'] = 'Order already confirmed'
        return response

    db.execute(
        'DELETE FROM orders '
        'WHERE order_id = ?',
        (order_id,)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/delete-from-order/<order_id>/<cart_id>', methods=["DELETE"])
@login_required
def delete_from_order(order_id, cart_id):
    response = {
        'isSuccess': False,
        'message': 'Delete shopping cart item'
    }

    db = get_db()

    db.execute(
        'DELETE FROM orders '
        'WHERE order_id = ? AND cart_id = ?',
        (order_id, cart_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response
