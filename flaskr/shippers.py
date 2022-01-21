import uuid
from datetime import datetime

from flask import Blueprint, g, request, jsonify

from flaskr.auth import login_required, authorization_required
from flaskr.db import get_db

bp = Blueprint('shippers', __name__, url_prefix='/shippers')


@bp.route('/create-shippers', methods=['POST'])
@login_required
@authorization_required
def add_product():
    response = {
        'isSuccess': False,
        'operation': 'Create Shipper'
    }

    db = get_db()

    body = dict(request.get_json())
    creation_data = {}
    creation_data['created_at'] = datetime.now()
    creation_data['created_by'] = g.user['username']

    for shipper in body['shippers']:
        shipper.update(creation_data)
        shipper['shipper_id'] = str(uuid.uuid4())

        try:
            db.execute(
                f'INSERT INTO shipper (shipper_id, shipper_name, phone_number, created_at, created_by) VALUES (?, ?, ?, ?, ?)',
                (
                    shipper['shipper_id'],
                    shipper['shipper_name'],
                    shipper['phone_number'],
                    shipper['created_at'],
                    shipper['created_by']
                ),
            )
            db.commit()
        except db.IntegrityError:
            response['message'] = f'Product {shipper["shipper_name"]} already exists.'
            pass

    response['total_inserted_shippers'] = len(body['shippers'])
    response['inserted_shippers'] = body['shippers']
    response['isSuccess'] = True
    return response


@bp.route('/create-shipment', methods=['POST'])
@login_required
@authorization_required
def create_shipment():
    response = {
        'isSuccess': False,
        'operation': 'Create Shipper'
    }

    db = get_db()
    username = g.user['username']
    created_at = datetime.now()

    body = dict(request.get_json())

    for order_id in body['order_ids']:
        check_order = db.execute(
            'SELECT shipper_id FROM order_info '
            'WHERE order_id = ? '
            'LIMIT 1',
            (order_id,)
        ).fetchall()

        if len(check_order) == 0:
            response['error'] = f'No such product with the id = {order_id}'
            return response

        if dict(check_order[0])['shipper_id'] is not None:
            response['error'] = f'Order {order_id} already shipped'
            return response

    for order_id in body['order_ids']:
        db.execute(
            'UPDATE order_info SET shipper_id = ?, date_shipped = ?, shipment_created_by = ? '
            'WHERE order_id = ?',
            (body['shipper_id'], created_at, username, order_id)
        )
        db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/all-shippers', methods=['GET'])
@login_required
@authorization_required
def all_shippers():
    db = get_db()
    shippers = db.execute(
        'SELECT * FROM shipper '
        'ORDER BY shipper_name ASC'
    ).fetchall()

    results = []

    for i in shippers:
        results.append(dict(i))

    return jsonify({
        'isSuccess': True,
        'total_products': len(results),
        'shippers': results
    })
