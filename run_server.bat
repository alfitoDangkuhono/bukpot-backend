@echo off
REM BPPU PDF Extractor - Start Server

echo Starting BPPU PDF Extractor API...
echo Server will run at http://localhost:8000
echo.
echo API Documentation:
echo - Swagger UI: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop server
echo.

python -m uvicorn app:app --reload --port 8000 --host 0.0.0.0
