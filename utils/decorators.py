from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    """Contoh pakai: @role_required('kaprodi') atau @role_required('kaprodi', 'dosen')"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def kaprodi_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_kaprodi:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function