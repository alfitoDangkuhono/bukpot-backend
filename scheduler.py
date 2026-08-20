import schedule
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Direktori uploads
UPLOAD_DIR = Path("uploads")


def delete_pdf_files():
    """Menghapus semua file PDF di folder uploads"""
    try:
        if not UPLOAD_DIR.exists():
            logger.warning(f"Folder {UPLOAD_DIR} tidak ditemukan")
            return
        
        pdf_files = list(UPLOAD_DIR.rglob("*.pdf"))
        
        if not pdf_files:
            logger.info("Tidak ada file PDF untuk dihapus")
            return
        
        # Hapus setiap file PDF
        deleted_count = 0
        logger.info(f"Mulai menghapus {len(pdf_files)} file PDF")
        
        for pdf_file in pdf_files:
            try:
                pdf_file.unlink()  # Using pathlib.Path.unlink() instead of os.remove()
                logger.info(f"✓ File dihapus: {pdf_file.name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"✗ Gagal menghapus {pdf_file.name}: {str(e)}")

        for job_dir in sorted(UPLOAD_DIR.iterdir(), reverse=True):
            if job_dir.is_dir():
                try:
                    job_dir.rmdir()
                except OSError:
                    pass
        
        logger.info(f"✓ Total file PDF yang dihapus: {deleted_count}")
        
    except Exception as e:
        logger.error(f"Error dalam delete_pdf_files: {str(e)}")


# Schedule untuk menghapus PDF setiap hari pukul 00:00 (tengah malam)
schedule.every().day.at("00:00").do(delete_pdf_files)

# Alternative: Hapus setiap jam (uncomment jika ingin ini)
# schedule.every().hour.do(delete_pdf_files)

# Alternative: Hapus setiap 6 jam sekali (uncomment jika ingin ini)
# schedule.every(6).hours.do(delete_pdf_files)

logger.info(f"Scheduler dimulai - Akan menghapus PDF setiap 00:00")

try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check schedule setiap 60 detik
except KeyboardInterrupt:
    logger.info("Scheduler dihentikan")