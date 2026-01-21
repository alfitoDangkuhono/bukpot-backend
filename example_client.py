"""
Example client untuk BPPU PDF Extractor API
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8443"

def health_check():
    """Check API health"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:")
    print(json.dumps(response.json(), indent=2))
    print()


def upload_pdfs(pdf_files: list[str]):
    """Upload multiple PDF files"""
    print(f"Uploading {len(pdf_files)} file(s)...")
    
    files = [
        ("files", open(pdf_file, "rb"))
        for pdf_file in pdf_files
        if Path(pdf_file).exists()
    ]
    
    if not files:
        print("No valid PDF files found!")
        return
    
    try:
        response = requests.post(f"{BASE_URL}/uploads", files=files)
        result = response.json()
        
        print(f"Upload Result:")
        print(f"  Total files: {result['total_files']}")
        print(f"  Success: {result['success']}")
        print(f"  Failed: {result['failed']}")
        
        if result['errors']:
            print(f"  Errors: {result['errors']}")
        
        print(f"\n  First record:")
        # if result['results']:
        #     first_data = result['results'][0]['data']
        #     print(f"    - Nomor: {first_data.get('Nomor Bukti Potong')}")
        #     print(f"    - Masa Pajak: {first_data.get('Masa Pajak')}")
        #     print(f"    - Nama Penerima: {first_data.get('Nama Penerima')}")
        #     print(f"    - PPh Dipotong: {first_data.get('PPh Dipotong')}")
        # print()
        
    finally:
        for _, file in files:
            file.close()


def get_results():
    """Get all extracted results"""
    print("Fetching results...")
    response = requests.get(f"{BASE_URL}/results")
    result = response.json()
    
    print(f"Results: {result['total_records']} records")
    
    if result['records']:
        print("\nFirst 3 records:")
        for i, record in enumerate(result['records'][:3], 1):
            print(f"  {i}. {record.get('Nomor Bukti Potong')} ({record.get('Masa Pajak')})")
    print()


def export_excel():
    """Export to Excel"""
    print("Exporting to Excel...")
    response = requests.get(f"{BASE_URL}/export")
    result = response.json()
    
    print(f"Export Result:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    print(f"  File: {result['file']}")
    print(f"  Total records: {result['total_records']}")
    print()


def clear_data():
    """Clear all data"""
    print("Clearing data...")
    response = requests.post(f"{BASE_URL}/clear")
    result = response.json()
    print(f"Clear Result: {result['message']}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("BPPU PDF Extractor - Example Client")
    print("=" * 60)
    print()
    
    # Health check
    try:
        health_check()
    except Exception as e:
        print(f"Error: Cannot connect to API")
        print(f"Make sure server is running: python -m uvicorn app:app --reload")
        exit(1)
    
    # Upload PDFs from pdfs folder
    pdf_files = list(Path("pdfs").glob("*.pdf"))[:3]  # First 3 PDFs
    
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF files in pdfs/ folder")
        upload_pdfs([str(f) for f in pdf_files])
        
        # Get results
        get_results()
        
        # Export to Excel
        export_excel()
    else:
        print("No PDF files found in pdfs/ folder")
    
    print("Done!")
