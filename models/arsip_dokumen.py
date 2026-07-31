from extensions import db
from datetime import datetime

arsip_allowed_users = db.Table(
    'arsip_dokumen_allowed_users',
    db.Column('arsip_id', db.Integer, db.ForeignKey('arsip_dokumen.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class ArsipDokumen(db.Model):
    """Model untuk Arsip Dokumen (Link URL dengan Kontrol Akses User)."""
    __tablename__ = 'arsip_dokumen'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    link_url = db.Column(db.Text, nullable=False)

    # Akses: 'semua' (semua user) atau 'custom' (user tertentu)
    akses_tipe = db.Column(db.String(20), nullable=False, default='semua')

    is_aktif = db.Column(db.Boolean, nullable=False, default=True, server_default='1')
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    uploader = db.relationship('User', foreign_keys=[uploader_id], backref='arsip_uploaded', lazy=True)
    allowed_users = db.relationship('User', secondary=arsip_allowed_users, backref='arsip_akses_diberikan', lazy=True)

    @property
    def url(self):
        return self.link_url or '#'

    def __repr__(self):
        return f'<ArsipDokumen id={self.id} nama={self.nama}>'
