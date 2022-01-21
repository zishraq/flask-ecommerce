import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return {
                'isSuccess': True,
                'message': 'No session'
            }

        return view(**kwargs)

    return wrapped_view


def authorization_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user['role'] != 'admin':
            return {
                'isSuccess': True,
                'message': 'Unauthorized'
            }

        return view(**kwargs)

    return wrapped_view


@bp.route('/register', methods=['POST'])
def register():
    response = {
        'isSuccess': False,
        'operation': 'Register'
    }

    body = dict(request.get_json())

    if 'username' not in body or 'password' not in body:
        response['error'] = 'Username or password missing'
        return response

    username = body['username']
    password = body['password']

    db = get_db()

    if not username:
        response['error'] = 'Username is required.'
        return response

    elif not password:
        response['error'] = 'Password is required.'
        return response

    try:
        # db.execute(
        #     'INSERT INTO user (username, password) VALUES (?, ?)',
        #     (username, generate_password_hash(password)),
        # )

        db.execute(
            'INSERT INTO user (username, password, role) VALUES (?, ?, ?)',
            (username, generate_password_hash(password), 'customer'),
        )

        db.commit()
    except db.IntegrityError:
        response['error'] = f'User {username} is already registered.'
        return response

    response['isSuccess'] = True
    return response

@bp.route('/grant-admin-permission', methods=['POST'])
@login_required
@authorization_required
def grant_admin_permission():
    response = {
        'isSuccess': False,
        'operation': 'Grant Admin permission'
    }
    db = get_db()

    body = dict(request.get_json())

    for username in body['usernames']:
        db.execute(
            'UPDATE user SET role = ? '
            'WHERE username = ?',
            ('admin', username)
        )
        db.commit()

    response['isSuccess'] = True
    return response


@bp.route('/login', methods=['POST'])
def login():
    response = {
        'isSuccess': False,
        'operation': 'Log In'
    }

    body = dict(request.get_json())

    if 'username' not in body or 'password' not in body:
        response['error'] = 'Username or password missing'
        return response

    username = body['username']
    password = body['password']

    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        response['error'] = 'Incorrect username.'
        return response

    if username == 'admin':
        if not password == user['password']:
            response['error'] = 'Incorrect password.'
            return response

    else:
        if not check_password_hash(user['password'], password):
            response['error'] = 'Incorrect password.'
            return response

    session.clear()
    session['username'] = user['username']
    response['isSuccess'] = True
    return response


@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return {
        'isSuccess': True,
        'operation': 'Successfully logged out'
    }


@bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    response = {
        'isSuccess': False,
        'operation': 'Account deleted'
    }

    body = dict(request.get_json())

    db = get_db()
    username = g.user['username']
    password = body['password']

    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if not check_password_hash(user['password'], password):
        response['error'] = 'Incorrect password.'
        return response

    db.execute(
        'DELETE FROM user '
        'WHERE username = ?',
        (username,)
    )
    db.commit()

    response['isSuccess'] = True
    return response
