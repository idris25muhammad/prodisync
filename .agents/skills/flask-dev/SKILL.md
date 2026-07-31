---
name: flask-dev
description: Dynamic developer instructions and rules for Flask backend architecture, secure code practices, minimalist UI design, and high-quality UX feedback.
---

# 🚀 Agent Development Guidelines & Persona

Aturan dan panduan ini wajib diikuti oleh AI Agent saat membantu atau memproduksi kode/solusi. Pengguna adalah seorang **Flask Web Developer** yang sangat mengandalkan modularitas, keamanan, desain bersih minimalis, serta performa UX yang solid.

---

## 🏛️ 1. Architecture & Backend (Flask & MVC Modularity)

* **Arsitektur Modular (Application Factory & Blueprints):**
  * Selalu gunakan **Application Factory Pattern** (`create_app()`).
  * Organisasikan fitur menggunakan **Flask Blueprints** secara terpisah (misal: `auth`, `dashboard`, `api`).
  * Terapkan pola **MVC (Model-View-Controller)** / Service Layer:
    * **Model:** Hanya untuk struktur database & ORM (SQLAlchemy).
    * **View/Template:** Jinja2 template render atau JSON payload response.
    * **Controller/Service:** Pisahkan logic bisnis dari route handler jika sudah kompleks.

* **Project Structure Standard:**
  ```text
  project_root/
  ├── app/
  │   ├── __init__.py          # Application Factory
  │   ├── models/              # SQLAlchemy Models
  │   ├── static/              # CSS, SVG Icons, JS
  │   ├── templates/           # Modular Jinja2 templates
  │   └── views/               # Blueprints (Controllers)
  │       ├── auth/
  │       └── main/
  ├── config.py                # Environment configs
  └── run.py                   # Entry point
  ```

---

## 🔒 2. Secure Code Practices (Prioritas Utama)

Setiap baris kode backend maupun integrasi wajib mematuhi standar keamanan:

1. **Input Validation & Sanitization:**
   * Jangan pernah mempercayai input pengguna. Gunakan **WTForms** atau **Marshmallow** untuk validasi schema.
2. **Authentication & Authorization:**
   * Simpan password menggunakan hashing kuat (`werkzeug.security` / `bcrypt`).
   * Terapkan penanganan role/akses (RBAC) dan pastikan decorator `@login_required` terpasang pada proteksi route.
3. **Database Security:**
   * Gunakan SQLAlchemy ORM parameter binding secara eksklusif. **Dilarang keras** melakukan string formatting/concatenation query SQL (Mencegah SQL Injection).
4. **CSRF & Security Headers:**
   * Wajib aktifkan **Flask-WTF CSRF Protection** pada semua method state-changing (POST, PUT, DELETE).
   * Terapkan header keamanan (CORS, Content-Security-Policy, X-Frame-Options) dengan tepat.
5. **Environment & Secrets:**
   * Pindahkan semua `SECRET_KEY`, Database URI, dan credentials sensitif ke environment variable (`.env` via `python-dotenv`).

---

## 🎨 3. Design System (Clean Minimalist)

UI harus tampil modern, elegan, dan profesional tanpa elemen dekoratif yang tidak perlu.

* **Typography-First:**
  * Fokus utama visual ada pada hirarki tipografi yang tegas, mudah dibaca, dan kontras.
* **Skema Warna (Maksimal 3 Warna):**
  * **Primary Background:** Dark Theme (e.g., `#0F172A` / Slate 900 atau Slate 950).
  * **Secondary / Card Background:** Elevated Dark (e.g., `#1E293B` / Slate 800).
  * **Accent Color:** 1 warna mencolok untuk CTA & Highlight (e.g., Emerald `#10B981` atau Electric Blue `#3B82F6`).
* **Icons:**
  * **Hanya gunakan SVG Solid/Monochrome inline**. Dilarang memakai font icon berat seperti FontAwesome via CDN jika bisa diwakili SVG ringan.
* **Whitespace & Layout:**
  * Gunakan **whitespace yang longgar (generous spacing)**. Bebaskan layout dari kepadatan elemen (`padding` dan `gap` yang lebar).

---

## 💡 4. User Experience (UX > UI)

Desain yang indah tidak ada artinya jika membingungkan pengguna. **UX adalah prioritas tertinggi.**

1. **Explicit Feedback & States:**
   * Setiap aksi form atau async request wajib menyediakan feedback yang jelas (Success/Error Toast, Loading State, Micro-interactions).
2. **Error Handling & Flash Messages:**
   * Berikan pesan kesalahan yang informatif dan membantu pengguna menyelesaikan masalah, bukan sekadar "Error Occurred".
3. **Navigation & Accessibility:**
   * Layout intuitif dengan alur navigasi seminimal mungkin. Kontras warna wajib memenuhi standar aksesibilitas dasar (WCAG).

---

## 🎯 Cara Memandu Agent

Saat memberikan perintah baru:
* AI Agent harus selalu menyajikan kode yang **siap pakai, terstruktur, dan mengikuti arsitektur modular**.
* Menghindari kode monolitik dalam satu file besar.
* Mengutamakan keamanan dan keringanan aset (SVG inline, minimal CSS dependencies).
