from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    """Contoh pakai: @role_required('kajur', 'kaprodi')"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def kaprodi_required(f):
    """Dapat diakses oleh kaprodi maupun pimpinan di atasnya (kajur/admin)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_kaprodi or current_user.is_kajur):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def kurikulum_required(f):
    """Dapat diakses oleh tim kurikulum, kaprodi/kps, maupun kajur/admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage_kurikulum:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def kajur_required(f):
    """Khusus untuk Ketua Jurusan / Admin Jurusan."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_kajur:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function