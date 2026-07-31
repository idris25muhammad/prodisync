from extensions import db
from datetime import datetime


class Agenda(db.Model):
    """Model untuk Agenda Kegiatan / Calendar Event."""
    __tablename__ = 'agenda'

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    tanggal = db.Column(db.Date, nullable=False)
    waktu_mulai = db.Column(db.Time, nullable=True)
    waktu_selesai = db.Column(db.Time, nullable=True)
    lokasi = db.Column(db.String(255), nullable=True)
    kategori = db.Column(db.String(50), nullable=True, default='Rapat Umum') # Rapat umum, rapat nilai, rapat RPS, rapat ATS, Workshop, Asesmen PBL, Lainnya

    is_aktif = db.Column(db.Boolean, nullable=False, default=True, server_default='1')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    creator = db.relationship('User', foreign_keys=[created_by], backref='agenda_created', lazy=True)

    def __repr__(self):
        return f'<Agenda id={self.id} judul={self.judul} tgl={self.tanggal}>'
