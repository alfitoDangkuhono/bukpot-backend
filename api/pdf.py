"""
PDF API endpoints
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import logging
from extractor import extract_from_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.post("/extract")
async def extract_pdf(file: UploadFile = File(...)) -> dict:
    """
    Extract data from a single PDF file
    
    Args:
        file: PDF file to extract data from
    
    Returns:
        Extracted data dictionary
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Save temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        content = await file.read()
        temp_path.write_bytes(content)
        
        try:
            # Extract data
            data = extract_from_file(str(temp_path))
            return {
                "status": "success",
                "filename": file.filename,
                "data": data
            }
        finally:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-batch")
async def extract_batch_pdf(files: list[UploadFile] = File(...)) -> dict:
    """
    Extract data from multiple PDF files
    
    Args:
        files: List of PDF files to extract data from
    
    Returns:
        Dictionary with extracted data and statistics
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = {
        "total_files": len(files),
        "success": 0,
        "failed": 0,
        "data": [],
        "errors": []
    }
    
    for idx, file in enumerate(files, 1):
        try:
            # Validate file type
            if not file.filename.lower().endswith(".pdf"):
                results["failed"] += 1
                results["errors"].append({
                    "file": file.filename,
                    "error": "File must be a PDF"
                })
                continue
            
            # Save temporarily
            temp_path = Path(f"/tmp/{file.filename}")
            content = await file.read()
            temp_path.write_bytes(content)
            
            try:
                # Extract data
                data = extract_from_file(str(temp_path))
                data["file_name"] = file.filename
                results["data"].append(data)
                results["success"] += 1
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
        
        except Exception as e:
            logger.error(f"Error extracting {file.filename}: {str(e)}")
            results["failed"] += 1
            results["errors"].append({
                "file": file.filename,
                "error": str(e)
            })
    
    return results
