import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import shutil
import logging
import uuid
from extractor import extract_from_file
from datetime import datetime
from typing import Optional, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Direktori untuk upload
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Storage untuk hasil ekstraksi
class ExtractedDataStore:
    """Thread-safe storage untuk extracted data"""
    def __init__(self):
        self.data = []
        self._lock = asyncio.Lock()
    
    def add(self, item):
        self.data.append(item)
    
    def get_all(self):
        return self.data.copy()
    
    def clear(self):
        self.data = []
    
    def update(self, items):
        self.data = items.copy()

data_store = ExtractedDataStore()
conversion_queue: asyncio.Queue = asyncio.Queue()
jobs = {}
jobs_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(application: FastAPI):
    worker = asyncio.create_task(conversion_worker())
    try:
        yield
    finally:
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)


app = FastAPI(
    title="BPPU PDF Extractor API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_pdf_file(filename: Optional[str]) -> bool:
    """Validasi file adalah PDF"""
    if not filename:
        return False
    return filename.lower().endswith(".pdf")


def generate_excel(extracted_data: list, job_id: str) -> str:
    """Write a conversion result outside the request event loop."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = RESULTS_DIR / f"hasil_bppu_{timestamp}_{job_id[:8]}.xlsx"
    pd.DataFrame(extracted_data).to_excel(excel_file, index=False, engine="openpyxl")
    return excel_file.name


async def update_job(job_id: str, **changes):
    async with jobs_lock:
        jobs[job_id].update(changes)


async def conversion_worker():
    while True:
        job = await conversion_queue.get()
        job_id = job["job_id"]
        try:
            await update_job(job_id, status="processing")
            extracted_data = []
            errors = []

            for file_idx, file_path in enumerate(job["files"], 1):
                try:
                    data = await asyncio.to_thread(extract_from_file, str(file_path))
                    data["file_name"] = file_path.name.split("_", 1)[-1]
                    extracted_data.append(data)
                except Exception as error:
                    logger.exception("Gagal memproses %s", file_path.name)
                    errors.append({"file": file_path.name, "error": str(error)})
                logger.info("[%s/%s] Job %s selesai", file_idx, len(job["files"]), job_id)

            excel_filename = None
            if extracted_data:
                excel_filename = await asyncio.to_thread(generate_excel, extracted_data, job_id)
                data_store.update(extracted_data)

            status = "completed" if not errors else "partial"
            if not extracted_data:
                status = "failed"
            await update_job(
                job_id,
                status=status,
                success=len(extracted_data),
                failed=len(errors),
                excel_file=excel_filename,
                excel_download_url=f"/downloads/{excel_filename}" if excel_filename else None,
                errors=errors or None,
                completed_at=datetime.now().isoformat(),
            )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.exception("Job %s gagal", job_id)
            await update_job(job_id, status="failed", error=str(error), completed_at=datetime.now().isoformat())
        finally:
            conversion_queue.task_done()


@app.post("/uploads", status_code=202)
async def upload_pdfs(
    files: list[UploadFile] = File(...),
):
    """
    Save PDFs and enqueue the conversion job for the background worker.
    """
    
    if not files:
        logger.warning("Upload request tanpa file")
        raise HTTPException(status_code=400, detail="Tidak ada file yang diunggah")
    
    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    file_paths = []
    for file_idx, file in enumerate(files, 1):
        if not validate_pdf_file(file.filename):
            shutil.rmtree(job_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' harus berformat PDF")
        filename = Path(file.filename).name
        file_path = job_dir / f"{file_idx}_{filename}"
        file_path.write_bytes(await file.read())
        file_paths.append(file_path)

    async with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "total_files": len(file_paths),
            "success": 0,
            "failed": 0,
            "excel_file": None,
            "excel_download_url": None,
            "errors": None,
            "created_at": datetime.now().isoformat(),
        }
    await conversion_queue.put({"job_id": job_id, "files": file_paths})
    logger.info("Job %s masuk queue (%s file)", job_id, len(file_paths))
    return {
        "status": "queued",
        "job_id": job_id,
        "status_url": f"/jobs/{job_id}",
        "total_files": len(file_paths),
    }


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Return queue and conversion status for an upload job."""
    async with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job tidak ditemukan")
        return job.copy()


@app.post("/clear")
async def clear_data():
    """Clear extracted data and upload directory"""
    logger.info("Clearing all data and upload directory")
    
    data_store.clear()
    
    # Clear upload directory
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
        UPLOAD_DIR.mkdir(exist_ok=True)
    
    logger.info("Data dan upload directory berhasil dihapus")
    return {"message": "Data dan upload directory berhasil dihapus"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "queue_size": conversion_queue.qsize(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/results")
async def get_results():
    """Get all extracted results"""
    results = data_store.get_all()
    return {
        "total_records": len(results),
        "records": results
    }


@app.get("/downloads/{filename}")
async def download_excel(filename: str):
    """Download Excel file dari results directory"""
    try:
        file_path = RESULTS_DIR / filename
        
        # Validasi file exists dan berada di RESULTS_DIR
        if not file_path.exists():
            logger.warning(f"File not found: {filename}")
            raise HTTPException(status_code=404, detail="File tidak ditemukan")
        
        # Security check: ensure path is within RESULTS_DIR
        if not str(file_path.resolve()).startswith(str(RESULTS_DIR.resolve())):
            logger.error(f"Invalid path attempt: {filename}")
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        logger.info(f"Downloading file: {filename}")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-files")
async def list_files():
    """List semua file yang tersedia untuk download"""
    try:
        excel_files = sorted(RESULTS_DIR.glob("*.xlsx"), reverse=True)
        pdf_files = sorted(UPLOAD_DIR.glob("*.pdf"), reverse=True)
        
        return {
            "excel_files": [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                    "download_url": f"/downloads/{f.name}"
                }
                for f in excel_files
            ],
            "pdf_files": [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
                }
                for f in pdf_files
            ]
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)
