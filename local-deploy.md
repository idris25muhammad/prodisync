# Local Deployment Guide — ProdiSync

Panduan ini menjelaskan cara menjalankan **ProdiSync** secara lokal di laptop atau PC lain dari awal (clone/pull dari GitHub) hingga aplikasi siap digunakan lengkap dengan data dari `database/prodisync_dml.sql`.

> **Catatan Arsitektur Database:**  
> - **DDL (struktur tabel, index, foreign key)** dikelola oleh Flask-Migrate / Alembic melalui `flask db upgrade`.  
> - **DML (data existing)** disimpan di [`database/prodisync_dml.sql`](database/prodisync_dml.sql) menggunakan `REPLACE INTO` dan mengecualikan tabel `alembic_version` agar tidak bentrok dengan riwayat migrasi.

---

## Prasyarat

Pastikan perangkat target sudah terpasang:
- **Git**
- **Python 3.10+** (disarankan 3.11 / 3.12 / 3.13)
- **MySQL Server 8.0** (running di `localhost:3306`)

---

## 1. Clone atau Pull Repository dari GitHub

### Jika baru pertama kali (Clone)
```bash
git clone https://github.com/idris25muhammad/prodisync.git
cd prodisync
```

### Jika repository sudah ada (Pull update terbaru)
```bash
cd prodisync
git pull
```

---

## 2. Buat Virtual Environment & Install Dependensi

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
> Jika muncul error execution policy saat mengaktifkan `venv`, jalankan terlebih dahulu:  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### macOS / Linux (Bash)
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Konfigurasi File `.env`

Salin `.env.example` menjadi `.env`:

### Windows (PowerShell)
```powershell
Copy-Item .env.example .env
```

### macOS / Linux
```bash
cp .env.example .env
```

Buka `.env` dan sesuaikan isinya dengan kredensial MySQL lokal Anda:

```env
# Flask
SECRET_KEY=ganti_dengan_secret_key_random_yang_kuat
FLASK_DEBUG=True

# Database
DB_USER=root
DB_PASSWORD=password_mysql_anda
DB_HOST=localhost
DB_PORT=3306
DB_NAME=prodisync_db
```

> **Penting:** `SECRET_KEY` wajib diisi (jika kosong, aplikasi akan error saat startup).

---

## 4. Buat Database Kosong di MySQL

Masuk ke MySQL shell lalu buat database `prodisync_db` dengan charset `utf8mb4`:

```sql
CREATE DATABASE IF NOT EXISTS prodisync_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Jika menggunakan command line sekali jalan:

### Windows (PowerShell)
```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "CREATE DATABASE IF NOT EXISTS prodisync_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### macOS / Linux
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS prodisync_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

## 5. Jalankan Migrasi Database (DDL)

Pastikan `venv` masih aktif, lalu jalankan:

```bash
flask db upgrade
```

Perintah ini akan membuat seluruh tabel, relasi foreign key, dan menandai revisi Alembic ke versi terbaru (`head`).

---

## 6. Import Data DML (`database/prodisync_dml.sql`)

Setelah migrasi selesai, import data dari `database/prodisync_dml.sql`:

### Windows (PowerShell)
Jika `mysql` sudah ada di `PATH`:
```powershell
Get-Content -Raw -Encoding UTF8 database\prodisync_dml.sql | mysql -u root -p --default-character-set=utf8mb4 prodisync_db
```

Jika `mysql` belum ada di `PATH` (default instalasi MySQL 8.0 di Windows):
```powershell
Get-Content -Raw -Encoding UTF8 database\prodisync_dml.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p --default-character-set=utf8mb4 prodisync_db
```

### Windows (CMD)
```cmd
mysql -u root -p --default-character-set=utf8mb4 prodisync_db < database\prodisync_dml.sql
```

### macOS / Linux
```bash
mysql -u root -p --default-character-set=utf8mb4 prodisync_db < database/prodisync_dml.sql
```

> **Alternatif GUI (MySQL Workbench / DBeaver / phpMyAdmin):**  
> Pilih database `prodisync_db`, lalu jalankan/import file `database/prodisync_dml.sql`.

---

## 7. Jalankan Aplikasi

Dengan `venv` aktif:

```bash
python app.py
```

Aplikasi berjalan di:
- **URL:** `http://127.0.0.1:5000`

Daftar akun uji coba yang tersedia di data hasil import dapat dilihat di [`akun.md`](akun.md) (misalnya `kajur` / `kajur123`, `kps` / `kps123`, `fulan` / `fulan123`).

---

## Pembaruan Selanjutnya (Setelah `git pull`)

Jika nanti ada update kode dan migrasi baru dari GitHub:

```bash
git pull
pip install -r requirements.txt
flask db upgrade
python app.py
```

---

## Troubleshooting Singkat

1. **`ValueError: SECRET_KEY belum diset di file .env!`**  
   Pastikan file `.env` berada di root folder project (`prodisync/.env`) dan `SECRET_KEY` tidak kosong.
2. **`mysql` is not recognized (Windows)**  
   Gunakan path lengkap `"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"` atau tambahkan folder `bin` MySQL ke Environment Variables `PATH`.
3. **Koneksi MySQL gagal (`Access denied` / `Can't connect`)**  
   Pastikan service MySQL 8.0 sedang berjalan (`services.msc` di Windows) dan `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` di `.env` sesuai.
