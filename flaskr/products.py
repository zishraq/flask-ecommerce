import uuid
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

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
    creation_data = {}
    creation_data['created_at'] = datetime.now()
    creation_data['created_by'] = g.user['username']
    creation_data['total_sold'] = 0

    for product in body['products']:
        product.update(creation_data)
        product['product_id'] = str(uuid.uuid4())

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

    body = dict(body[0])
    update_body = dict(request.get_json())
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
            'ORDER BY total_sold DESC'
        ).fetchall()
    else:
        products = db.execute(
            'SELECT product_id, product_name, description, product_category, price, discount FROM product '
            'ORDER BY total_sold DESC'
        ).fetchall()

    results = []

    for i in products:
        results.append(dict(i))

    return jsonify({
        'isSuccess': True,
        'total_products': len(results),
        'products': results
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
        search_term = search_term[1 : len(search_term) - 1]
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
