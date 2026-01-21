# BPPU PDF Extractor API

Backend web untuk ekstraksi data dari file PDF Bukti Pemotongan dan/atau Pemungutan PPh (BPPU).

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Server
```bash
python -m uvicorn app:app --reload
```

Server akan berjalan di `http://localhost:8000`

### 3. API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check
```
GET /health
```
Status check server

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Upload & Extract Multiple PDFs
```
POST /upload
```
Upload multiple PDF files dan ekstrak data otomatis

**Request:**
- Multipart form dengan file array
- Max files per request: unlimited

**Response:**
```json
{
  "total_files": 3,
  "success": 3,
  "failed": 0,
  "results": [
    {
      "file": "bppu_001.pdf",
      "status": "success",
      "data": {
        "No": "25001712N",
        "Nomor Bukti Potong": "25001712N",
        "Masa Pajak": "01-2025",
        "Sifat": "TIDAK FINAL",
        "Pembetulan": "NORMAL",
        "Kode Objek Pajak": "24-100-02",
        "Objek Pajak": "Royalti",
        "Jumlah Penghasilan Bruto": 38110959.0,
        "Tarif": 2.0,
        "PPh Dipotong": 762219.0,
        ...
      }
    }
  ],
  "errors": null
}
```

---

### 3. Extract Single PDF
```
POST /extract-single
```
Ekstrak satu PDF file

**Request:**
- Multipart form dengan satu file PDF

**Response:**
```json
{
  "status": "success",
  "file": "bppu_001.pdf",
  "data": {
    "No": "25001712N",
    ...
  }
}
```

---

### 4. Get Results
```
GET /results
```
Dapatkan semua hasil ekstraksi yang tersimpan di memory

**Response:**
```json
{
  "total_records": 3,
  "records": [
    {
      "No": "25001712N",
      "Nomor Bukti Potong": "25001712N",
      ...
    }
  ]
}
```

---

### 5. Export to Excel
```
GET /export
```
Export semua hasil ekstraksi ke file Excel

**Response:**
```json
{
  "status": "success",
  "message": "File berhasil diekspor",
  "file": "results/hasil_bppu_20240121_143022.xlsx",
  "total_records": 3
}
```

---

### 6. Clear Data
```
POST /clear
```
Hapus semua data yang tersimpan dan upload directory

**Response:**
```json
{
  "message": "Data dan upload directory berhasil dihapus"
}
```

---

## Data Fields

Setiap record ekstraksi berisi fields berikut:

| Field | Type | Deskripsi |
|-------|------|-----------|
| No | string | Nomor bukti potong (8 karakter) |
| Nomor Bukti Potong | string | Nomor bukti potong |
| Masa Pajak | string | Format MM-YYYY |
| Sifat | string | TIDAK FINAL / FINAL |
| Pembetulan | string | NORMAL / PEMBETULAN / DIBATALKAN |
| NPWP/NIK Penerima | string | NPWP atau NIK penerima |
| Nama Penerima | string | Nama penerima penghasilan |
| Jenis Fasilitas | string | Jenis fasilitas pajak |
| Jenis PPh | string | Jenis PPh (Pasal 23, 26, dll) |
| Kode Objek Pajak | string | Format XX-XXX-XX |
| Objek Pajak | string | Deskripsi objek pajak |
| Jumlah Penghasilan Bruto | float | Dalam Rupiah |
| Tarif | float | Tarif pajak dalam persen |
| PPh Dipotong | float | Dalam Rupiah |
| Jenis Dokumen | string | Jenis dokumen dasar |
| Nomor Dokumen | string | Nomor dokumen |
| Npwp Pemotong | string | NPWP pemotong |
| Nama Pemotong | string | Nama pemotong |
| Tanggal Bukti Potong | string | Tanggal pembuatan bukti potong |
| Tahun Pajak | string | Tahun pajak |

---

## Example Usage

### Using curl

**Upload files:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@bppu_001.pdf" \
  -F "files=@bppu_002.pdf"
```

**Get results:**
```bash
curl -X GET "http://localhost:8000/results"
```

**Export to Excel:**
```bash
curl -X GET "http://localhost:8000/export"
```

### Using Python requests

```python
import requests

# Upload files
files = [
    ('files', open('bppu_001.pdf', 'rb')),
    ('files', open('bppu_002.pdf', 'rb'))
]

response = requests.post('http://localhost:8000/upload', files=files)
print(response.json())

# Get results
response = requests.get('http://localhost:8000/results')
print(response.json())

# Export
response = requests.get('http://localhost:8000/export')
print(response.json())
```

---

## Directory Structure

```
.
├── app.py              # FastAPI application
├── extractor.py        # PDF extraction logic
├── requirements.txt    # Python dependencies
├── uploads/           # Temporary upload directory
├── results/           # Exported Excel files
└── pdfs/              # Sample PDFs (optional)
```

---

## Notes

- Hasil ekstraksi disimpan in-memory (akan hilang jika server restart)
- Untuk production, gunakan database untuk menyimpan hasil
- File upload tersimpan di `uploads/` directory
- Exported Excel file tersimpan di `results/` directory
