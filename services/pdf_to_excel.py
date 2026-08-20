import pdfplumber
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def process_pdf(file_path: str) -> Optional[Dict]:
    """
    Process PDF file and extract structured data
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Dictionary with extracted data or None if processing fails
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            
            # Extract text from all pages
            for page in pdf.pages:
                page_text = page.extract_text(layout=True)
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n".join(text_parts)
            
            # Basic data extraction
            data = {
                "file_path": file_path,
                "page_count": len(pdf.pages),
                "text_length": len(full_text)
            }
            
            return data
            
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        return None


def create_excel_from_data(
    data_list: List[Dict],
    output_path: str,
    sheet_name: str = "Data"
) -> bool:
    """
    Create Excel file from extracted data
    
    Args:
        data_list: List of dictionaries containing extracted data
        output_path: Path where Excel file will be saved
        sheet_name: Name of the worksheet
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not data_list:
            logger.warning("No data to create Excel file")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(data_list)
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to Excel
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Excel file created successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating Excel file: {str(e)}")
        return False


def batch_process_pdfs(
    pdf_files: List[str],
    output_excel_path: str
) -> Dict:
    """
    Process multiple PDF files and create Excel output
    
    Args:
        pdf_files: List of PDF file paths
        output_excel_path: Path for output Excel file
    
    Returns:
        Dictionary with processing results and statistics
    """
    results = {
        "total_files": len(pdf_files),
        "processed": 0,
        "failed": 0,
        "data": [],
        "errors": []
    }
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        try:
            logger.info(f"Processing [{idx}/{len(pdf_files)}] {pdf_file}")
            
            data = process_pdf(pdf_file)
            if data:
                results["data"].append(data)
                results["processed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "file": pdf_file,
                    "error": "Failed to extract data"
                })
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}")
            results["failed"] += 1
            results["errors"].append({
                "file": pdf_file,
                "error": str(e)
            })
    
    # Create Excel file if there's data
    if results["data"]:
        success = create_excel_from_data(results["data"], output_excel_path)
        results["excel_created"] = success
        results["excel_path"] = output_excel_path if success else None
    else:
        results["excel_created"] = False
        results["excel_path"] = None
    
    logger.info(
        f"Batch processing complete: "
        f"{results['processed']} processed, "
        f"{results['failed']} failed"
    )
    
    return results