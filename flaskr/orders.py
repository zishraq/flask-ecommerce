import uuid
from datetime import datetime

from flask import Blueprint, g, request

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('orders', __name__, url_prefix='/orders')


@bp.route('/make-order', methods=['POST'])
@login_required
def make_order():
    response = {
        'isSuccess': False,
        'message': 'Create an Order'
    }

    db = get_db()
    username = g.user['username']

    check_shopping_cart = db.execute(
        'SELECT * FROM shopping_cart_info '
        'WHERE username = ? '
        'ORDER BY created_at DESC '
        'LIMIT 1',
        (username,)
    ).fetchall()

    if len(check_shopping_cart) == 0:
        response['error'] = 'No products in the cart'
        return response

    else:
        shopping_cart_info = dict(check_shopping_cart[0])

        check_order = db.execute(
            'SELECT * FROM order_info '
            'WHERE order_id = ? '
            'LIMIT 1',
            (shopping_cart_info['cart_id'],)
        ).fetchall()

        if len(check_order) != 0:
            response['error'] = 'No products in the cart'
            return response

    order_id = shopping_cart_info['cart_id']
    created_at = datetime.now()

    check_product_status = db.execute(
        'SELECT p.product_id, p.product_name, p.in_stock, pbc.quantity FROM product AS p '
        'JOIN product_by_cart AS pbc '
        'ON p.product_id = pbc.product_id '
        'WHERE pbc.cart_id = ? ',
        (shopping_cart_info['cart_id'],)
    ).fetchall()

    for product in check_product_status:
        if product['in_stock'] < product['quantity']:
            response['error'] = f'Not enough {product["product_name"]}.'
            return response

    for product in check_product_status:
        db.execute(
            'UPDATE product SET in_stock = in_stock - ?, total_sold = total_sold + ?, updated_at = ? '
            'WHERE product_id = ?',
            (product['quantity'], product['quantity'], created_at, product['product_id'])
        )
        db.commit()

    body_details = request.get_json()

    if 'payment_method' not in body_details or 'address' not in body_details:
        response['error'] = 'Body key missing. payment_method or address.'
        return response

    try:
        db.execute(
            f'INSERT INTO order_info(order_id, created_at, payment_method, address) VALUES (?, ?, ?, ?)',
            (
                order_id,
                created_at,
                body_details['payment_method'],
                body_details['address']
            )
        )
        db.commit()

    except db.IntegrityError:
        response['error'] = f'Order id "{order_id}" already exists.'
        return response

    response['isSuccess'] = True
    response['order_id'] = order_id
    return response


@bp.route('/get-all-orders', methods=['GET'])
@login_required
def get_all_orders():
    response = {
        'isSuccess': False,
        'message': 'Create an Order'
    }

    username = g.user['username']

    db = get_db()

    orders = db.execute(
        'SELECT oi.order_id, oi.created_at, oi.payment_method, oi.address, pbc.product_id, pbc.quantity, p.product_name, p.price FROM order_info AS oi '
        'JOIN product_by_cart AS pbc '
        'ON oi.order_id = pbc.cart_id '
        'JOIN shopping_cart_info AS sci '
        'ON pbc.cart_id = sci.cart_id '
        'JOIN product AS p '
        'ON p.product_id = pbc.product_id '
        'WHERE sci.username = ?',
        (username,)
    ).fetchall()

    orders_categorised = {}

    for i in orders:
        formatted_data = dict(i)
        if formatted_data['order_id'] not in orders_categorised:
            orders_categorised[formatted_data['order_id']] = {
                'created_at': formatted_data['created_at'],
                'payment_method': formatted_data['payment_method'],
                'address': formatted_data['address'],
                'products': [
                    {
                        'product_id': formatted_data['product_id'],
                        'product_name': formatted_data['product_name'],
                        'price': formatted_data['price'],
                        'quantity': formatted_data['quantity']
                    }
                ]
            }
        else:
            orders_categorised[formatted_data['order_id']]['products'].append(
                {
                    'product_id': formatted_data['product_id'],
                    'product_name': formatted_data['product_name'],
                    'price': formatted_data['price'],
                    'quantity': formatted_data['quantity']
                }
            )

        # orders_categorised[]
        # print(dict(i))

    response['isSuccess'] = True
    response['orders'] = orders_categorised
    return response
