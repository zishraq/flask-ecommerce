import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['POST'])
def register():
    body = dict(request.get_json())
    error = None

    print(body)

    if 'username' not in body or 'password' not in body:
        print('here')
        error = 'Username or password missing'
        return {
            'isSuccess': False,
            'message': error
        }

    username = body['username']
    password = body['password']

    db = get_db()

    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'

    if error is None:
        try:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password)),
            )
            db.commit()
        except db.IntegrityError:
            error = f'User {username} is already registered.'
        else:
            # return redirect(url_for("auth.login"))
            return {
                'isSuccess': True,
                'message': 'Successfully registered'
            }
    return {
        'isSuccess': False,
        'message': error
    }


@bp.route('/login', methods=['POST'])
def login():
    # if request.method == 'POST':
    # username = request.form['username']
    # password = request.form['password']

    username = request.get_json()['username']
    password = request.get_json()['password']

    db = get_db()
    error = None
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        error = 'Incorrect username.'
    elif not check_password_hash(user['password'], password):
        error = 'Incorrect password.'

    if error is None:
        session.clear()
        session['user_id'] = user['id']
        # return redirect(url_for('index'))
        return {
            'isSuccess': True,
            'message': 'Successfully logged in'
        }

    return {
        'isSuccess': False,
        'error': error
    }
        # flash(error)

    # return render_template('auth/login.html')
    # return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
