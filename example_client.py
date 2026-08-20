"""
Example client untuk BPPU PDF Extractor API
"""

import requests
import json
import time
from pathlib import Path
from typing import List

BASE_URL = "http://localhost:8443"


def health_check():
    """Check API health"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check:")
        print(json.dumps(response.json(), indent=2))
        print()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return False


def upload_pdfs(pdf_files: List[str]) -> dict:
    """Upload multiple PDF files"""
    print(f"Uploading {len(pdf_files)} file(s)...")
    
    files = []
    try:
        # Build file list with context managers
        for pdf_file in pdf_files:
            if Path(pdf_file).exists():
                files.append(("files", open(pdf_file, "rb")))
        
        if not files:
            print("No valid PDF files found!")
            return {}
        
        try:
            response = requests.post(f"{BASE_URL}/uploads", files=files)
            result = response.json()
            
            print(f"Upload Result:")
            print(f"  Job ID: {result.get('job_id')}")
            job_url = f"{BASE_URL}{result.get('status_url')}"
            while result.get("status") in {"queued", "processing"}:
                time.sleep(1)
                result = requests.get(job_url).json()
            print(f"  Status: {result.get('status')}")
            print(f"  Success: {result.get('success')}")
            print(f"  Failed: {result.get('failed')}")
            if result.get('excel_file'):
                print(f"  Excel file: {result['excel_file']}")
                print(f"  Download URL: {result.get('excel_download_url')}")
            print()
            
            return result
            
        finally:
            # Properly close all file handles
            for _, file in files:
                file.close()
    
    except Exception as e:
        print(f"Error uploading files: {e}")
        return {}


def get_results() -> dict:
    """Get all extracted results"""
    print("Fetching results...")
    try:
        response = requests.get(f"{BASE_URL}/results")
        result = response.json()
        
        print(f"Results: {result['total_records']} records")
        
        if result.get('records'):
            print("\nFirst 3 records:")
            for i, record in enumerate(result['records'][:3], 1):
                nomor = record.get('Nomor Bukti Potong', 'N/A')
                masa = record.get('Masa Pajak', 'N/A')
                print(f"  {i}. {nomor} ({masa})")
        print()
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching results: {e}")
        return {}


def list_files() -> dict:
    """List all available files for download"""
    print("Listing available files...")
    try:
        response = requests.get(f"{BASE_URL}/list-files")
        result = response.json()
        
        print(f"Excel files: {len(result.get('excel_files', []))}")
        for file_info in result.get('excel_files', [])[:5]:
            size_mb = file_info.get('size', 0) / (1024 * 1024)
            print(f"  - {file_info.get('name')} ({size_mb:.2f} MB)")
        
        print(f"PDF files: {len(result.get('pdf_files', []))}")
        print()
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error listing files: {e}")
        return {}


def clear_data() -> dict:
    """Clear all data"""
    print("Clearing all data...")
    try:
        response = requests.post(f"{BASE_URL}/clear")
        result = response.json()
        print(f"Clear Result: {result.get('message')}")
        print()
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error clearing data: {e}")
        return {}


def main():
    """Main execution"""
    print("=" * 60)
    print("BPPU PDF Extractor - Example Client")
    print("=" * 60)
    print()
    
    # Health check
    if not health_check():
        print("Error: Cannot connect to API")
        print("Make sure server is running: python -m uvicorn app:app --reload")
        return
    
    # Find PDF files
    pdf_files = list(Path("pdfs").glob("*.pdf"))[:3]  # First 3 PDFs
    
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF files in pdfs/ folder\n")
        
        # Upload PDFs
        upload_pdfs([str(f) for f in pdf_files])
        
        # Get results
        get_results()
        
        # List files
        list_files()
    else:
        print("No PDF files found in pdfs/ folder")
    
    print("Done!")


if __name__ == "__main__":
    main()
