from extensions import db
from datetime import datetime

class Pengumuman(db.Model):
    __tablename__ = 'pengumuman'

    id         = db.Column(db.Integer, primary_key=True)
    judul      = db.Column(db.String(255), nullable=False)
    konten     = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default='draft')  # draft | dosen | publik
    file_path  = db.Column(db.String(255), nullable=True)  # optional attachment

    penulis_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    penulis    = db.relationship('User', backref='pengumuman', lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Pengumuman {self.judul}>'
