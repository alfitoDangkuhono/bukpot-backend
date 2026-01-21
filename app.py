from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import shutil
from extractor import extract_from_file
from datetime import datetime

# Setup
app = FastAPI(title="BPPU PDF Extractor API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Direktori untuk upload
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Storage untuk hasil ekstraksi
extracted_data = []


@app.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...), download_only: bool = Query(False)):
    """Upload multiple PDF files, ekstrak data, dan generate Excel otomatis
    
    Query parameters:
    - download_only: jika True, response hanya berisi info download Excel
    """
    global extracted_data
    
    if not files:
        raise HTTPException(status_code=400, detail="Tidak ada file yang diunggah")
    
    errors = []
    extracted_data = []
    
    for file in files:
        try:
            # Validasi file type
            if not file.filename.lower().endswith(".pdf"):
                errors.append({
                    "file": file.filename,
                    "error": "File harus berformat PDF"
                })
                continue
            
            # Save file
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            # Ekstrak data
            data = extract_from_file(str(file_path))
            data["file_name"] = file.filename
            extracted_data.append(data)
            
        except Exception as e:
            errors.append({
                "file": file.filename,
                "error": str(e)
            })
    
    # Generate Excel otomatis setelah ekstraksi
    excel_file = None
    if extracted_data:
        try:
            df = pd.DataFrame(extracted_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = RESULTS_DIR / f"hasil_bppu_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            excel_filename = excel_file.name
        except Exception as e:
            errors.append({
                "file": "Excel Export",
                "error": f"Gagal generate Excel: {str(e)}"
            })
            excel_filename = None
    else:
        excel_filename = None
    
    # Jika download_only = True, hanya return info download
    if download_only:
        return {
            "status": "success" if excel_filename else "failed",
            "excel_file": excel_filename,
            "excel_download_url": f"/download-excel/{excel_filename}" if excel_filename else None,
            "total_records": len(extracted_data)
        }
    
    # Full response
    return {
        "total_files": len(files),
        "success": len(extracted_data),
        "failed": len(errors),
        "excel_file": excel_filename,
        "excel_download_url": f"/download-excel/{excel_filename}" if excel_filename else None,
        "errors": errors if errors else None
    }


@app.post("/clear")
async def clear_data():
    """Clear extracted data"""
    global extracted_data
    extracted_data = []
    
    # Clear upload directory
    shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    return {"message": "Data dan upload directory berhasil dihapus"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/download-excel/{filename}")
async def download_excel(filename: str):
    """Download Excel file dari results directory"""
    try:
        file_path = RESULTS_DIR / filename
        
        # Validasi file exists dan berada di RESULTS_DIR
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File tidak ditemukan")
        
        if not str(file_path.resolve()).startswith(str(RESULTS_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-files")
async def list_files():
    """List semua file yang tersedia untuk download"""
    try:
        excel_files = list(RESULTS_DIR.glob("*.xlsx"))
        pdf_files = list(UPLOAD_DIR.glob("*.pdf"))
        
        return {
            "excel_files": [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                    "download_url": f"/download-excel/{f.name}"
                }
                for f in sorted(excel_files, reverse=True)
            ],
            "pdf_files": [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
                }
                for f in sorted(pdf_files, reverse=True)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
