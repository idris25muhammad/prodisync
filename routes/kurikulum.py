from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from extensions import db
from models import MataKuliah, TahunAjaran

bp = Blueprint('kurikulum', __name__, url_prefix='/kurikulum')


@bp.route('/matakuliah')
@login_required
def matakuliah():
    return redirect(url_for('matakuliah.list'))


@bp.route('/integrated')
@login_required
def integrated():
    return render_template('kurikulum/integrated.html')


@bp.route('/prasyarat')
@login_required
def prasyarat():
    return render_template('kurikulum/prasyarat.html')