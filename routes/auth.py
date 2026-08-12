from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models import User
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()
bp = Blueprint('auth', __name__)

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        if user:
            try:
                ph.verify(user.password, request.form.get('password'))

                # Argon2 rehash otomatis jika parameter berubah
                if ph.check_needs_rehash(user.password):
                    user.password = ph.hash(request.form.get('password'))
                    db.session.commit()

                logout_user()
                login_user(user)
                resp = make_response(redirect(url_for('dashboard.index')))
                resp.delete_cookie('remember_token')
                return resp
            except VerifyMismatchError:
                pass

        flash('Username atau Password salah!', 'danger')
        return render_template('login.html')
    # GET: hapus session + remember_token stale
    logout_user()
    resp = make_response(render_template('login.html'))
    resp.delete_cookie('remember_token')
    return resp


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie('remember_token')
    return resp