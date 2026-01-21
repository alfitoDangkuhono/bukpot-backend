@echo off
REM BPPU PDF Extractor - Start Server & Scheduler

echo Starting BPPU PDF Extractor API and Scheduler...
echo Server will run at http://localhost:8443
echo.
echo API Documentation:
echo - Swagger UI: http://localhost:8443/docs
echo - ReDoc: http://localhost:8443/redoc
echo.
echo Scheduler: Menghapus PDF setiap 10 detik
echo.
echo Press Ctrl+C to stop server
echo.

REM Jalankan scheduler di background
start "PDF Scheduler" python scheduler.py

REM Jalankan FastAPI server
python -m uvicorn app:app --reload --port 8443 --host 0.0.0.0
