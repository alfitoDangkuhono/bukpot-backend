#!/bin/bash

echo "Starting BPPU PDF Extractor API and Scheduler..."
echo "Server will run at http://localhost:8443"
echo ""
echo "API Documentation:"
echo "- Swagger UI: http://localhost:8443/docs"
echo "- ReDoc: http://localhost:8443/redoc"
echo ""
echo "Scheduler: Menghapus PDF setiap jam 00:00"
echo ""
echo "Press Ctrl+C to stop server"
echo ""

# Jalankan scheduler di background
python scheduler.py &

# Simpan PID scheduler biar bisa dihentikan nanti
SCHEDULER_PID=$!

# Jalankan FastAPI server (foreground)
gunicorn app:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8443 \
  --workers 1 \
  --timeout 120

# Kalau server berhenti, matikan scheduler juga
kill $SCHEDULER_PID
