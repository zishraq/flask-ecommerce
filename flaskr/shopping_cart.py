import uuid
from datetime import datetime

from flask import Blueprint, g, request

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('shopping_cart', __name__, url_prefix='/shopping-cart')


@bp.route('/add-to-cart', methods=["POST"])
@login_required
def create_shopping_cart():
    response = {
        'isSuccess': False,
        'message': 'Products added to shopping cart'
    }

    db = get_db()
    username = g.user['username']
    created_at = datetime.now()
    is_new_cart = False

    check_shopping_cart = db.execute(
        'SELECT * FROM shopping_cart_info '
        'WHERE username = ? '
        'ORDER BY created_at DESC '
        'LIMIT 1',
        (username,)
    ).fetchall()

    if len(check_shopping_cart) == 0:
        cart_id = str(uuid.uuid4())
        is_new_cart = True

    else:
        shopping_cart_info = dict(check_shopping_cart[0])

        check_order = db.execute(
            'SELECT * FROM order_info '
            'WHERE order_id = ? '
            'LIMIT 1',
            (shopping_cart_info['cart_id'],)
        ).fetchall()

        if len(check_order) != 0:
            print('stuck here 2')
            cart_id = str(uuid.uuid4())
            is_new_cart = True

        else:
            cart_id = shopping_cart_info['cart_id']

    if is_new_cart:
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

    added_products = request.get_json()['products']

    for product in added_products:
        check_product = db.execute(
            'SELECT * FROM product '
            'WHERE product_id = ? '
            'LIMIT 1',
            (product['product_id'],)
        ).fetchall()

        if len(check_product) == 0:
            response['error'] = f'No such product with the id = {product["product_id"]}'
            return response

        previous_status = db.execute(
            'SELECT * FROM product_by_cart '
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
                f'INSERT INTO product_by_cart(cart_id, product_id, quantity, added_at) VALUES (?, ?, ?, ?)',
                (
                    cart_id,
                    product['product_id'],
                    product['quantity'],
                    created_at
                )
            )
            db.commit()
        except db.IntegrityError:
            db.execute(
                'UPDATE product_by_cart SET quantity = ?, updated_at = ? '
                'WHERE cart_id = ? AND product_id = ?',
                (product['quantity'], created_at, cart_id, product['product_id'])
            )
            db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/get-products-in-cart', methods=['GET'])
@login_required
def get_products_by_cart():
    response = {
        'isSuccess': False,
        'operation': 'Get products in the cart'
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

        print(username)
        print(shopping_cart_info)

        check_order = db.execute(
            'SELECT * FROM order_info '
            'WHERE order_id = ? '
            'LIMIT 1',
            (shopping_cart_info['cart_id'],)
        ).fetchall()

        if len(check_order) != 0:
            response['error'] = 'No products in the cart'
            return response

        else:
            cart_id = shopping_cart_info['cart_id']

    products = db.execute(
        'SELECT pbc.product_id, p.product_name, pbc.quantity, sci.username, sci.created_at, sci.updated_at, SUM((p.price - p.discount) * pbc.quantity) AS product_total_price '
        'FROM product_by_cart AS pbc '
        'JOIN product AS p '
        'ON pbc.product_id = p.product_id '
        'JOIN shopping_cart_info AS sci '
        'ON sci.cart_id = pbc.cart_id '
        'WHERE pbc.cart_id = ? '
        'GROUP BY pbc.product_id '
        'ORDER BY sci.created_at ASC ',
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
    response['username'] = username
    response['created_at'] = created_at
    response['updated_at'] = updated_at
    response['total_price'] = round(total_price, 2)
    response['products'] = results
    return response


@bp.route('/delete-from-shopping-cart/<product_id>', methods=["DELETE"])
@login_required
def delete_from_shopping_cart(product_id):
    response = {
        'isSuccess': False,
        'message': 'Delete shopping cart item'
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

        else:
            cart_id = shopping_cart_info['cart_id']

    check_product_in_cart = db.execute(
        'SELECT * FROM product_by_cart '
        'WHERE cart_id = ? AND product_id = ? '
        'LIMIT 1',
        (cart_id, product_id)
    ).fetchall()

    if len(check_product_in_cart) == 0:
        response['error'] = 'No such product'
        return response

    db.execute(
        'DELETE FROM product_by_cart '
        'WHERE cart_id = ? AND product_id = ?',
        (cart_id, product_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response
