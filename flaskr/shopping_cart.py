import uuid
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('shopping_cart', __name__)


@bp.route('/create-shopping-cart', methods=["POST"])
@login_required
def create_shopping_cart():
    response = {
        'isSuccess': False,
        'message': 'Create a shopping cart'
    }

    cart_id = str(uuid.uuid4())
    username = g.user['username']

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


@bp.route('/add-to-cart/<cart_id>', methods=['PUT'])
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
