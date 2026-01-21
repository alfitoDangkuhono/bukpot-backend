import pdfplumber
import pandas as pd
import io


def process_pdf(file):
    text = ""

    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)  # Gunakan layout=True
            if page_text:
                text += page_text + "\n"
    
    data = {
        
    }