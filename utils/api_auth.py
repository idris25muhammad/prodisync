from datetime import datetime
from functools import wraps
from flask import request, jsonify, g
from extensions import db
from models.api_client import ApiClient


def api_error(status: int, code: str, message: str):
    """Format respons error JSON yang konsisten untuk REST API."""
    return jsonify({'error': {'code': code, 'message': message}}), status


def api_key_required(f):
    """
    Decorator autentikasi REST API menggunakan header `X-API-Key`.
    Memverifikasi hash key, status aktif, lalu mencatat statistik pemakaian.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        raw_key = (request.headers.get('X-API-Key') or '').strip()
        if not raw_key:
            return api_error(401, 'missing_api_key', 'Header X-API-Key wajib disertakan.')

        client = ApiClient.find_by_raw_key(raw_key)
        if not client or not client.is_active:
            return api_error(401, 'invalid_api_key', 'API key tidak valid atau tidak aktif.')

        g.api_client = client

        try:
            client.request_count = (client.request_count or 0) + 1
            client.last_used_at = datetime.now()
            client.last_used_ip = request.headers.get('X-Real-IP') or request.remote_addr
            db.session.commit()
        except Exception:
            db.session.rollback()

        return f(*args, **kwargs)
    return decorated
