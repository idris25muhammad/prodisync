import hashlib
import hmac
import secrets
from extensions import db


class ApiClient(db.Model):
    """Klien sistem internal yang diizinkan mengakses REST API ProdiSync."""
    __tablename__ = 'api_client'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    description   = db.Column(db.String(255), nullable=True)
    key_prefix    = db.Column(db.String(20), unique=True, nullable=False, index=True)
    key_hash      = db.Column(db.String(64), nullable=False)
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    last_used_at  = db.Column(db.DateTime, nullable=True)
    last_used_ip  = db.Column(db.String(45), nullable=True)
    request_count = db.Column(db.Integer, nullable=False, default=0)
    created_by    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_at    = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at    = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    creator       = db.relationship('User', foreign_keys=[created_by], lazy=True)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    @classmethod
    def generate_key(cls):
        """
        Buat API key baru dengan format `psk_<8hex>_<secret>`.
        Return tuple (full_key, key_prefix, key_hash).
        """
        prefix_id = secrets.token_hex(4)  # 8 karakter hex
        secret = secrets.token_urlsafe(32)
        key_prefix = f"psk_{prefix_id}"
        full_key = f"{key_prefix}_{secret}"
        return full_key, key_prefix, cls.hash_key(full_key)

    def verify_key(self, raw_key: str) -> bool:
        if not raw_key:
            return False
        return hmac.compare_digest(self.key_hash, self.hash_key(raw_key))

    @classmethod
    def find_by_raw_key(cls, raw_key: str):
        """Cari ApiClient berdasarkan prefix dan verifikasi hash-nya."""
        if not raw_key or not raw_key.startswith('psk_'):
            return None
        parts = raw_key.split('_', 2)
        if len(parts) != 3:
            return None
        prefix = f"{parts[0]}_{parts[1]}"
        client = cls.query.filter_by(key_prefix=prefix).first()
        if not client or not client.verify_key(raw_key):
            return None
        return client

    def __repr__(self):
        return f'<ApiClient {self.name} ({self.key_prefix})>'
