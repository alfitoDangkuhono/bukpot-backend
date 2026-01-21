# Quick Start Guide

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server
**Windows:**
```bash
run_server.bat
```

**Linux/Mac:**
```bash
python -m uvicorn app:app --reload --port 8000
```

Server akan berjalan di: **http://localhost:8000**

---

## Access API Documentation

Buka browser dan kunjungi:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Quick Test

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Upload PDF Files
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@pdfs/sample1.pdf" \
  -F "files=@pdfs/sample2.pdf"
```

### 3. Get Results
```bash
curl http://localhost:8000/results
```

### 4. Export to Excel
```bash
curl http://localhost:8000/export
```

---

## Using Python Client

```bash
python example_client.py
```

---

## Troubleshooting

### Server tidak start
- Pastikan port 8000 tidak digunakan aplikasi lain
- Cek apakah FastAPI terinstall: `pip list | grep fastapi`

### Import error
- Install ulang requirements: `pip install -r requirements.txt --force-reinstall`

### PDF tidak bisa diekstraksi
- Pastikan file adalah PDF valid
- Cek format BPPU sudah sesuai standar

---

## File Structure

```
.
├── app.py                 # FastAPI aplikasi utama
├── extractor.py          # Logika ekstraksi PDF
├── example_client.py     # Contoh client
├── requirements.txt      # Dependencies
├── README.md            # Dokumentasi lengkap
├── run_server.bat       # Script run server (Windows)
├── pdfs/                # Folder untuk sample PDFs
├── uploads/             # Temporary upload directory (auto-created)
└── results/             # Output Excel files (auto-created)
```

---

## API Response Format

Semua response dalam format JSON:

```json
{
  "status": "success",
  "data": {...},
  "error": null
}
```

---

## Next Steps

1. Tambahkan database untuk persistent storage
2. Implement authentication & authorization
3. Add file size limits & rate limiting
4. Setup CI/CD pipeline
5. Deploy ke production server

---

For detailed documentation, see **README.md**
