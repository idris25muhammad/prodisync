from flask import Blueprint, render_template, request, redirect, url_for, flash
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

                login_user(user)
                return redirect(url_for('dashboard.index'))
            except VerifyMismatchError:
                pass

        flash('Username atau Password salah!', 'danger')
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))