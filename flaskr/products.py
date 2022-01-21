import uuid
from datetime import datetime

from flask import Blueprint, g, request, jsonify

from flaskr.auth import login_required, authorization_required
from flaskr.db import get_db

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/add-product', methods=['POST'])
@login_required
@authorization_required
def add_product():
    response = {
        'isSuccess': False,
        'operation': 'Add product'
    }

    db = get_db()

    body = dict(request.get_json())

    product_names = []

    if 'products' not in body:
        response['error'] = 'products key not provided'
        return response

    else:
        if type(body['products']) != list:
            response['error'] = 'products key should be a list or array'
            return response

        for product in body['products']:
            product_existence_check = product['product_name'] + product['description']

            if product_existence_check not in product_names:
                product_names.append(product_existence_check)
            else:
                response['error'] = f'Product {product["product_name"]} appeared more than once in the body.'
                return response

            if 'product_name' not in product or 'description' not in product or 'product_category' not in product or 'price' not in product or 'discount' not in product or 'in_stock' not in product:
                response['error'] = 'A key is missing.'
                response['product_details'] = product
                return response

    creation_data = {}
    creation_data['created_at'] = datetime.now()
    creation_data['created_by'] = g.user['username']
    creation_data['total_sold'] = 0

    for product in body['products']:
        product.update(creation_data)
        product['product_id'] = str(uuid.uuid4())

        check_product_name = db.execute(
            'SELECT product_name FROM product '
            'WHERE product_name = ? '
            'LIMIT 1',
            (product['product_name'],)
        ).fetchall()

        check_product_description = db.execute(
            'SELECT description FROM product '
            'WHERE description = ? '
            'LIMIT 1',
            (product['description'],)
        ).fetchall()

        if len(check_product_name) != 0 and len(check_product_description) != 0:
            response['error'] = f'Product {check_product_name[0]["product_name"]} already exists.'
            return response

        try:
            db.execute(
                f'INSERT INTO product (product_id, product_name, description, product_category, price, discount, created_at, created_by, in_stock, total_sold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    product['product_id'],
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

        if 'tags' in product:
            for tag in product['tags']:
                try:
                    db.execute(
                        f'INSERT INTO product_tags (tag_name, created_at, created_by) VALUES (?, ?, ?)',
                        (
                            tag,
                            creation_data['created_at'],
                            creation_data['created_by']
                        ),
                    )
                    db.commit()
                except db.IntegrityError:
                    pass

                db.execute(
                    f'INSERT INTO product_by_tag (tag_name, product_id) VALUES (?, ?)',
                    (
                        tag,
                        product['product_id'],
                    ),
                )
                db.commit()

    response['total_inserted_products'] = len(body['products'])
    response['inserted_products'] = body['products']
    response['isSuccess'] = True
    return response


@bp.route('/delete-product/<product_id>', methods=['DELETE'])
@login_required
@authorization_required
def delete_product(product_id):
    response = {
        'isSuccess': False,
        'message': 'Delete a product'
    }

    db = get_db()

    db.execute(
        'DELETE FROM product_by_cart '
        'WHERE product_id = ?',
        (product_id,)
    )
    db.commit()

    db.execute(
        'DELETE FROM product_wishlist '
        'WHERE product_id = ?',
        (product_id,)
    )
    db.commit()

    db.execute(
        'DELETE FROM product_by_tags '
        'WHERE product_id = ?',
        (product_id,)
    )
    db.commit()

    db.execute(
        'DELETE FROM product '
        'WHERE product_id = ?',
        (product_id,)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/update-product/<product_id>', methods=['PUT'])
@login_required
@authorization_required
def update_product(product_id):
    response = {
        'isSuccess': False,
        'operation': 'Update product'
    }

    db = get_db()

    update_body = dict(request.get_json())

    for key in update_body:
        if key not in ['product_name', 'description', 'product_category', 'price', 'discount', 'in_stock', 'tags']:
            response['error'] = 'Wrong key provided.'
            return response

        if key in ['product_name', 'description', 'product_category']:
            if type(update_body[key]) != str:
                response['error'] = f'Wrong type for {key}.'
                return response

        if key in ['price', 'discount']:
            if type(update_body[key]) not in [int, float]:
                response['error'] = f'Wrong type for {key}.'
                return response

        if key == 'in_stock':
            if type(update_body[key]) != int:
                response['error'] = 'Wrong type for product_name.'
                return response

        if key == 'tags':
            if type(update_body[key]) != list:
                response['error'] = 'Wrong type for tags.'
                return response

    body = db.execute(
        'SELECT * FROM product '
        'WHERE product_id = ? '
        'LIMIT 1',
        (product_id,)
    ).fetchall()

    if len(body) == 0:
        response['error'] = f'No such product with the id = {product_id}'
        return response

    db.execute(
        'DELETE FROM product '
        'WHERE product_id = ?',
        (product_id,)
    )
    db.commit()

    db.execute(
        'DELETE FROM product_by_tag '
        'WHERE product_id = ?',
        (product_id,)
    )
    db.commit()

    body = dict(body[0])

    update_data = {}
    update_data['updated_at'] = datetime.now()
    update_data['updated_by'] = g.user['username']

    body.update(update_body)
    body.update(update_data)

    try:
        db.execute(
            f'INSERT INTO product (product_id, product_name, description, product_category, price, discount, created_at, created_by, updated_at, updated_by, in_stock, total_sold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                body['product_id'],
                body['product_name'],
                body['description'],
                body['product_category'],
                body['price'],
                body['discount'],
                body['created_at'],
                body['created_by'],
                body['updated_at'],
                body['updated_by'],
                body['in_stock'],
                body['total_sold']
            ),
        )
        db.commit()
    except db.IntegrityError:
        response['error'] = f'Product {body["product_name"]} already exists.'
        return response

    if 'tags' in update_body:
        for tag in update_body['tags']:
            try:
                db.execute(
                    f'INSERT INTO product_tags (tag_name, created_at, created_by) VALUES (?, ?, ?)',
                    (
                        tag,
                        update_data['updated_at'],
                        update_data['updated_by']
                    ),
                )
                db.commit()
            except db.IntegrityError:
                pass

            db.execute(
                f'INSERT INTO product_by_tag (tag_name, product_id) VALUES (?, ?)',
                (
                    tag,
                    product_id,
                ),
            )
            db.commit()

    response['updated_products'] = body
    return response


@bp.route('/all-products', methods=['GET'])
@login_required
def all_products():
    db = get_db()

    username = g.user['username']

    get_role = db.execute(
        'SELECT role FROM user '
        'WHERE username = ?',
        (username,)
    ).fetchall()

    user_role = dict(get_role[0])['role']

    if user_role == 'admin':
        products = db.execute(
            'SELECT * FROM product '
            'ORDER BY created_at ASC'
        ).fetchall()

    else:
        products = db.execute(
            'SELECT product_id, product_name, description, product_category, price, discount FROM product '
            'WHERE in_stock > 0 '
            'ORDER BY total_sold DESC'
        ).fetchall()

    results = []

    for i in products:
        formatted_data = dict(i)

        get_product_tags = db.execute(
            'SELECT tag_name FROM product_by_tag '
            'WHERE product_id = ?',
            (formatted_data['product_id'],)
        ).fetchall()

        if user_role == 'admin':
            formatted_data['tags'] = []

            for tag in get_product_tags:
                formatted_data['tags'].append(dict(tag)['tag_name'])

        results.append(formatted_data)

    return jsonify({
        'isSuccess': True,
        'total_products': len(results),
        'products': results
    })


@bp.route('/product-details/<product_id>', methods=['GET'])
@login_required
def product_details(product_id):
    response = {
        'isSuccess': False,
        'operation': 'Get product details'
    }

    db = get_db()

    username = g.user['username']

    get_role = db.execute(
        'SELECT role FROM user '
        'WHERE username = ?',
        (username,)
    ).fetchall()

    user_role = dict(get_role[0])['role']

    if user_role == 'admin':
        products = db.execute(
            'SELECT * FROM product '
            'WHERE product_id = ? '
            'LIMIT 1',
            (product_id,)
        ).fetchall()

    else:
        products = db.execute(
            'SELECT product_id, product_name, description, product_category, price, discount FROM product '
            'WHERE product_id = ? AND in_stock > 0 '
            'LIMIT 1',
            (product_id,)
        ).fetchall()

    if len(products) == 0:
        response['error'] = f'No such product with the id = {product_id}'
        return response

    result = dict(products[0])

    if user_role == 'admin':
        get_product_tags = db.execute(
            'SELECT tag_name FROM product_by_tag '
            'WHERE product_id = ?',
            (product_id,)
        ).fetchall()

        get_orders = db.execute(
            'SELECT oi.order_id, pbc.quantity, sci.username FROM order_info AS oi '
            'JOIN product_by_cart AS pbc '
            'ON oi.order_id = pbc.cart_id '
            'JOIN shopping_cart_info AS sci '
            'ON pbc.cart_id = sci.cart_id '
            'WHERE pbc.product_id = ?',
            (product_id,)
        ).fetchall()

        result['tags'] = []
        result['orders'] = []

        for tag in get_product_tags:
            result['tags'].append(dict(tag)['tag_name'])

        for order in get_orders:
            result['orders'].append(
                {
                    dict(order)['order_id']: {
                        'username': dict(order)['username'],
                        'quantity': dict(order)['quantity']
                    }
                }
            )

    return jsonify({
        'isSuccess': True,
        'product': result
    })


@bp.route('/add-products-to-wishlist', methods=['POST'])
@login_required
def add_products_to_wishlist():
    response = {
        'isSuccess': False,
        'operation': 'Add product to wishlist'
    }

    db = get_db()

    body = dict(request.get_json())
    username = g.user['username']

    for product_id in body['product_ids']:
        check_product = db.execute(
            'SELECT product_id FROM product '
            'WHERE product_id = ? '
            'LIMIT 1',
            (product_id,)
        ).fetchall()

        if len(check_product) == 0:
            response['error'] = f'No such product with the id = {product_id}'
            return response

        try:
            db.execute(
                f'INSERT INTO product_wishlist (username, product_id) VALUES (?, ?)',
                (
                    username,
                    product_id
                ),
            )
            db.commit()
        except db.IntegrityError:
            response['message'] = f'Product {product_id} already added.'
            pass

    response['isSuccess'] = True
    return response


@bp.route('/remove-product-from-wishlist/<product_id>', methods=['POST'])
@login_required
def remove_product_from_wishlist(product_id):
    response = {
        'isSuccess': False,
        'operation': 'Remove product from wishlist'
    }

    db = get_db()
    username = g.user['username']

    check_wishlist = db.execute(
        'SELECT * FROM product_wishlist '
        'WHERE username = ? AND product_id = ? '
        'ORDER BY created_at DESC '
        'LIMIT 1',
        (username, product_id)
    ).fetchall()

    if len(check_wishlist) == 0:
        response['error'] = 'No such product in the wishlist'
        return response

    db.execute(
        'DELETE FROM product_wishlist '
        'WHERE username = ? AND product_id = ?',
        (username, product_id)
    )
    db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/wishlist-products', methods=['GET'])
@login_required
def wishlist_products():
    db = get_db()
    username = g.user['username']

    products = db.execute(
        'SELECT product_id, product_name, description, product_category, price, discount FROM product '
        'WHERE product_id IN (SELECT DISTINCT product_id FROM product_wishlist WHERE username = ?)',
        (username,)
    ).fetchall()

    results = []

    for i in products:
        results.append(dict(i))

    return jsonify({
        'isSuccess': True,
        'total_products': len(results),
        'products': results
    })


@bp.route('/search-products', methods=['GET'])
@login_required
def search_products():
    db = get_db()

    username = g.user['username']

    search_term = request.args.get('q')

    if ' ' in search_term:
        search_term_formatted = search_term.replace(' ', '%')
        search_term_formatted = f'%{search_term_formatted}%'
        print(search_term_formatted)

    else:
        search_term = search_term[1: len(search_term) - 1]
        search_term_formatted = f'%{search_term}%'

    get_role = db.execute(
        'SELECT role FROM user '
        'WHERE username = ?',
        (username,)
    ).fetchall()

    user_role = dict(get_role[0])['role']

    if user_role == 'admin':
        products_query = f'''
            SELECT * FROM product 
            WHERE LOWER(product_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(product_category) LIKE ? OR 
            product_id IN ( 
               SELECT product_id FROM product_by_tag WHERE tag_name LIKE ? 
           )
        '''

        print(products_query)

        products = db.execute(
            products_query, (search_term_formatted, search_term_formatted, search_term_formatted, search_term_formatted)
        ).fetchall()

    else:
        products_query = f'''
            SELECT product_id, product_name, description, product_category, price, discount FROM product 
            WHERE LOWER(product_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(product_category) LIKE ? OR 
            product_id IN ( 
               SELECT product_id FROM product_by_tag WHERE tag_name LIKE ? 
           )
        '''

        print(products_query)

        products = db.execute(
            products_query, (search_term_formatted, search_term_formatted, search_term_formatted, search_term_formatted)
        ).fetchall()

    results = []

    for i in products:
        results.append(dict(i))

    return jsonify({
        'isSuccess': True,
        'total_products': len(results),
        'products': results
    })
