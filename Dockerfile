# ─────────────────────────────────────────────
# Stage 1: Builder – install dependencies
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (untuk xhtml2pdf & argon2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dan install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt gunicorn

# ─────────────────────────────────────────────
# Stage 2: Runtime – image final yang ringan
# ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages dari builder
COPY --from=builder /install /usr/local

# Copy source code aplikasi
COPY . .

# Buat direktori storage dengan permission yang benar
RUN mkdir -p storage && chmod -R 755 storage

# Port yang di-expose (Gunicorn akan listen di sini)
EXPOSE 8000

# Health check untuk container
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Jalankan Gunicorn sebagai WSGI server
# - 4 worker (sesuaikan dengan CPU server: 2*CPU+1)
# - timeout 120s untuk generate PDF
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
