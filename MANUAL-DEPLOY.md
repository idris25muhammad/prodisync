# 🖥️ Panduan Manual Deployment (Tanpa Docker) di Linux / Ubuntu

Dokumen ini berisi panduan langkah demi langkah untuk melakukan instalasi dan deployment aplikasi **ProdiSync** secara langsung di server **Linux (Ubuntu Server 22.04 / 24.04 LTS)** menggunakan **Python Virtual Environment**, **Gunicorn**, **Systemd Service**, **MySQL**, dan **Nginx**.

---

## 📋 Prasyarat Sistem & Paket Server

Sebelum memulai, pastikan paket-paket berikut sudah terpasang di server Ubuntu:

- **Python 3.10** atau lebih baru & `python3-venv`
- **MySQL Server 8.0**
- **Nginx Web Server**
- **Git**

Jalankan perintah berikut untuk menginstal dependensi dasar:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential mysql-server nginx git
```

---

## 🚀 Langkah-Langkah Deployment

### 1. Clone Repository & Setup Virtual Environment

Letakkan aplikasi di direktori `/var/www/prodisync` atau `/opt/prodisync`:

```bash
sudo mkdir -p /var/www/prodisync
sudo chown -R $USER:$USER /var/www/prodisync
cd /var/www/prodisync

# Clone repository
git clone https://github.com/idris25muhammad/prodisync.git .

# Buat Python Virtual Environment
python3 -m venv venv
source venv/bin/activate
```

---

### 2. Install Dependensi Python & Gunicorn

Di dalam virtual environment yang aktif, install seluruh modul yang dibutuhkan beserta WSGI Server Gunicorn:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

### 3. Konfigurasi Environment Variables (`.env`)

Buat file `.env` dari template `.env.example`:

```bash
cp .env.example .env
nano .env
```

Sesuaikan isi variabel lingkungan:

```env
# Flask Configuration
SECRET_KEY=ganti_dengan_random_string_panjang_dan_aman_32_karakter
FLASK_DEBUG=False

# Database MySQL Configuration
DB_USER=prodisync_user
DB_PASSWORD=Password_Sangat_Kuat_123!
DB_HOST=localhost
DB_PORT=3306
DB_NAME=prodisync_db
```

> 💡 **Tips:** Generate `SECRET_KEY` yang aman dengan mengeksekusi:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

---

### 4. Setup Database MySQL

Masuk ke CLI MySQL root:

```bash
sudo mysql -u root -p
```

Eksekusi perintah SQL berikut untuk membuat database dan user:

```sql
CREATE DATABASE prodisync_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'prodisync_user'@'localhost' IDENTIFIED BY 'Password_Sangat_Kuat_123!';
GRANT ALL PRIVILEGES ON prodisync_db.* TO 'prodisync_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### 5. Inisialisasi & Migrasi Database

Pastikan virtual environment aktif, lalu jalankan perbaikan skema database dan penyiapan data awal:

```bash
# Upgrade skema database menggunakan Flask-Migrate (Alembic)
flask db upgrade

# Populate data user default & tahun ajaran
flask seed-db

# Populate data katalog mata kuliah
flask seed-matakuliah
```

---

### 6. Konfigurasi Systemd Service (Gunicorn Process Manager)

Agar aplikasi Flask (Gunicorn) berjalan secara otomatis di background dan hidup kembali secara otomatis saat server reboot, buat unit service Systemd.

Buat file service baru:

```bash
sudo nano /etc/systemd/system/prodisync.service
```

Isi dengan konfigurasi berikut:

```ini
[Unit]
Description=ProdiSync Flask Application Service
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/prodisync
Environment="PATH=/var/www/prodisync/venv/bin"
ExecStart=/var/www/prodisync/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile - "app:create_app()"
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Atur hak akses direktori agar dapat dibaca oleh pengguna `www-data`:

```bash
sudo chown -R www-data:www-data /var/www/prodisync
sudo chmod -R 755 /var/www/prodisync/storage
```

Muat ulang daemon Systemd, aktifkan, dan jalankan service `prodisync`:

```bash
sudo systemctl daemon-reload
sudo systemctl enable prodisync
sudo systemctl start prodisync
sudo systemctl status prodisync
```

---

### 7. Konfigurasi Nginx Server (Reverse Proxy)

Buat file konfigurasi virtual host Nginx:

```bash
sudo nano /etc/nginx/sites-available/prodisync
```

Isi file konfigurasi Nginx:

```nginx
server {
    listen 80;
    server_name yourdomain.com; # Ganti dengan nama domain atau IP server Anda

    client_max_body_size 20M;

    # Dynamic Proxy ke Gunicorn WSGI Server
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Pelayanan Aset Statis Langsung via Nginx (Optimasi Performa)
    location /static/ {
        alias /var/www/prodisync/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Pelayanan File Upload Storage
    location /storage/ {
        alias /var/www/prodisync/storage/;
        expires 7d;
    }
}
```

Aktifkan konfigurasi Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/prodisync /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🛠️ Perintah Pemeliharaan (Maintenance)

- **Mengecek status service aplikasi:**
  ```bash
  sudo systemctl status prodisync
  ```
- **Melihat log aplikasi real-time (Systemd Journal):**
  ```bash
  sudo journalctl -u prodisync -f
  ```
- **Melakukan restart service setelah update kode:**
  ```bash
  sudo systemctl restart prodisync
  ```
- **Menjalankan migrasi database setelah git pull:**
  ```bash
  cd /var/www/prodisync
  source venv/bin/activate
  flask db upgrade
  sudo systemctl restart prodisync
  ```
