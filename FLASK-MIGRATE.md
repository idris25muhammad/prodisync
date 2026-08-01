# 🗄️ Panduan Mekanisme Migrasi Database (Flask-Migrate / Alembic)

Dokumen ini adalah panduan operasional bagi pengembang aplikasi **ProdiSync** untuk melakukan pembaruan skema database di lingkungan pengembangan (Development) dan produksi (Production) menggunakan **Flask-Migrate** (berbasis **Alembic**).

---

## 📌 Konsep Dasar & Perintah Utama

Flask-Migrate melacak setiap perubahan skema database melalui skrip migrasi terversi yang tersimpan di dalam folder `migrations/versions/`. Setiap berkas migrasi memiliki fungsi `upgrade()` (menerapkan perubahan) dan `downgrade()` (membatalkan perubahan).

### Daftar Perintah CLI Penting:

| Perintah | Deskripsi Peran |
|---|---|
| `flask db migrate -m "pesan"` | Mendeteksi perubahan skema SQLAlchemy dan membuat berkas migrasi baru. |
| `flask db upgrade` | Menerapkan seluruh migrasi yang belum dieksekusi ke database. |
| `flask db downgrade` | Membatalkan (rollback) 1 tingkat migrasi terakhir. |
| `flask db current` | Menampilkan ID versi migrasi yang sedang aktif di database saat ini. |
| `flask db history` | Menampilkan riwayat urutan versi migrasi dari awal hingga akhir. |
| `flask db heads` | Menampilkan versi migrasi paling ujung (terbaru) yang terdaftar di repositori. |

---

## 🛠️ SKENARIO 1: Menambahkan Model atau Tabel Baru ke Production

Gunakan alur berikut saat Anda membuat fitur baru yang membutuhkan tabel database baru (misal: menambahkan modul **LogAktivitas** atau **KategoriArsip**).

### Langkah 1: Deklarasikan Model Baru

Buat file model baru di folder `models/` (misal: [models/kategori_arsip.py](file:///c:/idlabs/prodisync/models/kategori_arsip.py)):

```python
from extensions import db
from datetime import datetime

class KategoriArsip(db.Model):
    __tablename__ = 'kategori_arsip'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False, unique=True)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<KategoriArsip {self.nama}>'
```

### Langkah 2: Registrasikan Model pada `models/__init__.py`

Agar Alembic dapat mendeteksi model baru tersebut saat autogenerate, Anda **wajib mengimpor** model baru di berkas `models/__init__.py`:

```python
from models.user import User
from models.rps import RPS
from models.kategori_arsip import KategoriArsip  # <--- Import model baru disini

__all__ = ['User', 'RPS', 'KategoriArsip']
```

### Langkah 3: Generate File Migrasi (Di Lingkungan Development)

Jalankan perintah berikut di lingkungan pengembangan lokal Anda:

```bash
flask db migrate -m "Tambah tabel kategori_arsip"
```

Alembic akan membandingkan skema SQLAlchemy dengan database aktual dan membuat file migrasi baru di direktori `migrations/versions/xxxx_tambah_tabel_kategori_arsip.py`.

### Langkah 4: Verifikasi & Review File Migrasi

Buka file yang baru terbentuk di folder `migrations/versions/` dan pastikan fungsi `upgrade()` berisi kode pembuat tabel yang sesuai:

```python
def upgrade():
    op.create_table('kategori_arsip',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nama', sa.String(length=100), nullable=False),
        sa.Column('keterangan', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nama')
    )

def downgrade():
    op.drop_table('kategori_arsip')
```

### Langkah 5: Uji Coba Migrasi di Development

Jalankan migrasi di database lokal:

```bash
flask db upgrade
```

### Langkah 6: Commit Berkas Migrasi ke Git

Tambahkan file migrasi baru ke dalam Version Control (Git) agar dapat di-deploy ke server produksi:

```bash
git add models/ migrations/
git commit -m "feat: tambah model dan tabel kategori_arsip"
git push origin main
```

### Langkah 7: Penerapan di Lingkungan Production Server

Setelah kode di-pull ke server produksi, jalankan perintah upgrade:

- **Bila Menggunakan Docker Container:**
  ```bash
  docker compose exec prodisyncapp flask db upgrade
  ```
  *(Catatan: Apabila menggunakan CI/CD GitHub Actions, skrip deployment akan otomatis menjalankan perintah ini saat container restart).*

- **Bila Menggunakan Deployment Manual:**
  ```bash
  cd /var/www/prodisync
  source venv/bin/activate
  flask db upgrade
  ```

---

## 🔄 SKENARIO 2: Mengubah Kolom dari Tabel yang Sudah Ada

Mengubah tabel yang sudah menyimpan data di produksi memerlukan kehati-hatian ekstra agar data tidak hilang atau merusak aplikasi yang sedang berjalan.

---

### Kasus 2.1: Mengubah Nama Kolom (Rename Column)

Alembic autogenerate terkadang mendeteksi perubahan nama kolom sebagai **DROP COLUMN** lalu **ADD COLUMN** (yang akan **menghapus data lama** pada kolom tersebut!).

#### Cara Aman Melakukan Rename Kolom:

1. Ubah nama atribut di SQLAlchemy Model (misal: di `models/pengumuman.py`, ubah `deskripsi` menjadi `keterangan`).
2. Jalankan `flask db migrate -m "Rename deskripsi ke keterangan pada pengumuman"`.
3. **Buka file skrip migrasi yang baru dibuat** di `migrations/versions/`.
4. Jika skrip buatan otomatis berisi `op.drop_column` dan `op.add_column`, **ganti dengan `op.alter_column`**:

```python
# ❌ HINDARI KODE SEPERTI INI (Akan menghapus data):
# op.drop_column('pengumuman', 'deskripsi')
# op.add_column('pengumuman', sa.Column('keterangan', sa.Text(), nullable=True))

# ✅ GUNAKAN op.alter_column DENGAN new_column_name:
def upgrade():
    op.alter_column('pengumuman', 'deskripsi', new_column_name='keterangan')

def downgrade():
    op.alter_column('pengumuman', 'keterangan', new_column_name='deskripsi')
```

5. Jalankan `flask db upgrade`.

---

### Kasus 2.2: Mengubah Tipe Data atau Panjang Kolom

Contoh: Memperbesar kapasitas tipe data `kode_mk` pada tabel `matakuliah` dari `VARCHAR(10)` menjadi `VARCHAR(20)`.

1. Perbarui definisi atribut pada SQLAlchemy Model:
   ```python
   # models/matakuliah.py
   kode_mk = db.Column(db.String(20), nullable=False, unique=True) # Sebelumnya String(10)
   ```
2. Generate berkas migrasi:
   ```bash
   flask db migrate -m "Perbesar panjang kode_mk menjadi 20 karakter"
   ```
3. Periksa skrip migrasi yang dihasilkan:
   ```python
   def upgrade():
       op.alter_column('matakuliah', 'kode_mk',
                  existing_type=sa.String(length=10),
                  type_=sa.String(length=20),
                  existing_nullable=False)

   def downgrade():
       op.alter_column('matakuliah', 'kode_mk',
                  existing_type=sa.String(length=20),
                  type_=sa.String(length=10),
                  existing_nullable=False)
   ```
4. Jalankan `flask db upgrade`.

---

### Kasus 2.3: Menambahkan Kolom `NOT NULL` pada Tabel Berisi Data

Menambahkan kolom bernilai wajib (`nullable=False`) ke tabel produksi yang sudah berisi ribuan data tanpa memberikan nilai awal (default) akan memicu kegagalan migrasi (`IntegrityError`).

#### Cara Aman 2-Langkah:

1. **Definisikan kolom dengan `server_default` atau `nullable=True` terlebih dahulu:**
   ```python
   # Step 1: Berikan default value pada level database
   status = db.Column(db.String(20), nullable=False, server_default='aktif')
   ```
2. Jalankan `flask db migrate -m "Tambah kolom status dengan server_default"` dan `flask db upgrade`.
3. Setelah migrasi berhasil di-apply dan seluruh data lama memiliki nilai default `'aktif'`, Anda dapat menghapus `server_default` jika tidak lagi diperlukan.

---

### Kasus 2.4: Penggunaan Batch Alter (Alembic Batch Operations)

Pada database MySQL atau SQLite, beberapa operasi `ALTER TABLE` (seperti mengubah foreign key constraint atau unique index) dapat terkendala pembatasan engine database.

Jika Anda mengalami kendala alter constraint, gunakan konteks `batch_alter_table` di file migrasi:

```python
def upgrade():
    with op.batch_alter_table('rps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('revisi_ke', sa.Integer(), server_default='0', nullable=False))
        batch_op.create_index(batch_op.f('ix_rps_kode_mk'), ['kode_mk'], unique=False)

def downgrade():
    with op.batch_alter_table('rps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rps_kode_mk'))
        batch_op.drop_column('revisi_ke')
```

---

## ⚡ Best Practices & Mengatasi Masalah (Troubleshooting)

1. **Wajib Selalu Commit Folder `migrations/`**  
   Jangan memasukkan folder `migrations/` ke `.gitignore`. Folder ini menyimpan riwayat versi skema database yang harus sinkron di antara seluruh pengembang dan server produksi.

2. **Atasi Konflik Multiple Heads (`Multiple head revisions present`)**  
   Jika dua developer membuat migrasi secara bersamaan di branch terpisah, saat di-merge akan terjadi kondisi *multiple heads*.
   - Cek versi head:
     ```bash
     flask db heads
     ```
   - Gabungkan kedua head revision menjadi satu:
     ```bash
     flask db merge heads -m "Merge migration heads"
     ```
   - Terapkan migrasi hasil gabungan:
     ```bash
     flask db upgrade
     ```

3. **Gagal Migrasi di Production / Ingin Rollback**  
   Jika migrasi terbaru mengalami error saat di-apply di server produksi, Anda dapat membatalkan migrasi ke 1 revisi sebelumnya:
   ```bash
   flask db downgrade
   ```
   Lalu cek status revisi yang aktif:
   ```bash
   flask db current
   ```
