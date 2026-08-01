# ProdiSync

**ProdiSync** adalah sistem manajemen program studi berbasis web yang dirancang untuk mengelola **Rencana Pembelajaran Semester (RPS)**, kurikulum, pengumuman, agenda kegiatan, serta arsip dokumen secara terstruktur, aman, dan kolaboratif.

Aplikasi ini dibangun menggunakan **Flask 3.0** (Python), **MySQL 8.0**, **SQLAlchemy ORM**, dan **Jinja2 Templates**, serta dikembangkan dengan standar keamanan dan modulasi arsitektur modern.

---

## 🌟 Fitur & Modul Utama

| Modul | Deskripsi |
|---|---|
| **Autentikasi & Keamanan** | Login aman dengan algoritma password hashing Argon2 serta proteksi role-based access control (RBAC). |
| **Manajemen RPS** | Pembuatan, penyuntingan, pencetakan (PDF via `xhtml2pdf`), dan publikasi Rencana Pembelajaran Semester per mata kuliah. |
| **Katalog Mata Kuliah** | Pengelolaan daftar mata kuliah berdasarkan struktur kurikulum prodi. |
| **Kurikulum & Tahun Ajaran** | Pengaturan tahun ajaran aktif dan kurikulum yang berlaku. |
| **Pengumuman Prodi** | Publikasi pengumuman internal maupun publik untuk civitas akademika. |
| **Agenda & Jadwal** | Manajemen agenda dan jadwal kegiatan prodi. |
| **Arsip Dokumen** | Manajemen file & pengunggahan arsip dokumen prodi. |
| **Manajemen Pengguna** | Administrasi akun dosen dan pimpinan prodi (Kaprodi). |

---

## 👥 Aktor & Hak Akses Pengguna

Aplikasi ProdiSync membagi hak akses ke dalam 2 peran (aktor) utama:

```
                  ┌─────────────────────────────────────────┐
                  │            Aktor & Hak Akses            │
                  └────────────────────┬────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
      ┌─────────┴───────────┐                       ┌─────────┴───────────┐
      │     Role: DOSEN     │                       │    Role: KAPRODI    │
      └─────────┬───────────┘                       └─────────┬───────────┘
                │                                             │
   - Kelola RPS Mata Kuliah Milik Sendiri        - Akses Semua Fitur Dosen
   - Lihat Pengumuman & Agenda Prodi             - Kelola Seluruh Data RPS & Kurikulum
   - Lihat & Unduh Arsip Dokumen                 - Manajemen User (Tambah/Edit/Hapus)
   - Cetak PDF RPS                               - Kelola Pengumuman, Agenda & Arsip
```

1. **Dosen**
   - Membuat, menyunting, dan memperbarui RPS untuk mata kuliah yang diampu.
   - Mengunduh dan mencetak RPS dalam format PDF.
   - Mengakses agenda kegiatan prodi dan arsip dokumen.
2. **Kaprodi (Ketua Program Studi / Administrator)**
   - Hak akses penuh (*Full Administrative Control*).
   - Mengelola akun pengguna (Dosen dan Kaprodi).
   - Meninjau, menyetujui, dan mengelola seluruh RPS di lingkungan prodi.
   - Mengelola data master: Kurikulum, Tahun Ajaran, Katalog Mata Kuliah.
   - Menerbitkan pengumuman, mengelola agenda, dan mengunggah dokumen arsip.

---

## 🏗️ Arsitektur Aplikasi & Tech Stack

ProdiSync menerapkan **Application Factory Pattern** dan **Flask Blueprints** (MVC) untuk menjamin kerapihan dan skalabilitas kode:

- **Backend Framework**: Python 3.10+ & Flask 3.0
- **Database & ORM**: MySQL 8.0 + SQLAlchemy (via PyMySQL)
- **Database Migration**: Flask-Migrate (Alembic)
- **Password Hashing**: Argon2 (`argon2-cffi`)
- **PDF Engine**: `xhtml2pdf`
- **Template Engine**: Jinja2 HTML5 + CSS3 (Slate Dark Theme & Responsive UI)
- **WSGI Production Server**: Gunicorn

```
project_root/
├── app.py                  # Application Factory (`create_app()`) & CLI Seed Commands
├── config.py               # Konfigurasi Environment (Development, Production, Testing)
├── extensions.py           # Inisialisasi ekstensi Flask (db, login_manager, migrate)
├── requirements.txt        # Dependensi pustaka Python
├── .env.example            # Template variabel lingkungan
├── Dockerfile              # Dockerfile untuk image aplikasi Flask
├── docker-compose.yml      # Orkestrasi container Docker (prodisyncdb & prodisyncapp)
├── migrations/             # Berkas migrasi skema database (Alembic)
├── models/                 # Model-model SQLAlchemy (User, RPS, Matakuliah, dsb.)
├── routes/                 # Blueprint Controller (auth, rps, admin, dsb.)
├── templates/              # Modul Template Jinja2
├── static/                 # Aset statis (CSS, SVG Icons, JS)
└── storage/                # Direktori penyimpan unggahan arsip dokumen & media
```

---

## 📚 Dokumentasi Deployment & Migrasi

Dokumentasi telah dipisahkan berdasarkan kebutuhan operasional dan deployment. Silakan merujuk ke panduan yang sesuai:

1. 🐳 **[Panduan Deployment Docker Container (Ubuntu Server)](DOCKER-DEPLOY.md)**  
   *Panduan resmi deployment produksi menggunakan Docker Compose (`prodisyncdb` & `prodisyncapp`), Host Nginx Reverse Proxy di port 80/443, serta integrasi CI/CD GitHub Actions.*

2. 🖥️ **[Panduan Manual Deployment (Linux / Ubuntu)](MANUAL-DEPLOY.md)**  
   *Panduan deployment manual di server Linux tanpa Docker (Virtualenv, Gunicorn, Systemd Service, dan Host Nginx).*

3. 🗄️ **[Panduan Migrasi Database Flask-Migrate](FLASK-MIGRATE.md)**  
   *Panduan mekanisme pembaruan skema database di lingkungan produksi: 1. Menambahkan tabel/model baru; 2. Mengubah/mengubah nama kolom pada tabel yang sudah ada.*

---

## 🔐 Akun Akreditasi Default (Development / Seed)

Setelah menjalankan database seed, akun berikut secara otomatis tersedia:

| Username | Password | Peran (Role) |
|---|---|---|
| `idris` | `idris123` | Dosen |
| `kps` | `kps123` | Kaprodi |

> ⚠️ **Penting:** Selalu ubah password default saat melakukan deployment ke lingkungan produksi!

---

## 🏢 Pengembang

**IDLabs** — Program Studi Rekayasa Keamanan Siber, Politeknik Negeri Batam.