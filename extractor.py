import pdfplumber
import re
from typing import Dict, List, Optional


def extract_text_from_pdf(pdf_path: str) -> str:
    """Ekstrak text dari PDF dengan layout preservation"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)
            if page_text:
                text += page_text + "\n"
    return text


def convert_to_number(text_value: Optional[str]) -> Optional[float]:
    """Konversi text dengan format Indonesia (titik pemisah ribuan) ke number"""
    if not text_value:
        return None
    try:
        # Contoh: "1.234.567" -> "1234567" -> 1234567
        num_str = text_value.replace(".", "")
        return float(num_str)
    except:
        return None


def get_value(text: str, label_regex: str) -> str:
    """Ekstrak nilai dari text menggunakan regex pattern"""
    pattern = rf"{label_regex}\s*[:：]\s*(.+?)(?=\n|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def get_jenis_dokumen(text: str) -> str:
    """Ekstrak jenis dokumen"""
    match = re.search(
        r"B\.8\s+DOKUMEN DASAR BUKTI JENIS DOKUMEN\s*:\s*(.+?)\s+Tanggal",
        text,
        re.IGNORECASE
    )
    return match.group(1).strip() if match else ""


def extract_data(text: str) -> Dict:
    """Ekstrak semua data dari text PDF"""
    data = {}

    # --- HEADER ---
    nomor = re.search(r"([0-9A-Z]{8})\s+(\d{2}-\d{4})", text)
    no_val = nomor.group(1) if nomor else ""
    masa_val = nomor.group(2) if nomor else ""
    
    if not nomor:
        nomor = re.search(r"([0-9A-Z]{8})", text)
        no_val = nomor.group(1) if nomor else ""
        
        masa = re.search(r"(\d{2}-\d{4})", text)
        masa_val = masa.group(1) if masa else ""
    
    # Cari sifat
    sifat = re.search(r"(TIDAK\s+FINAL|FINAL)", text, re.IGNORECASE)
    sifat_val = sifat.group(1).strip() if sifat else ""
    
    # Cari pembetulan
    pembetulan = re.search(r"(NORMAL|PEMBETULAN|DIBATALKAN)", text, re.IGNORECASE)
    pembetulan_val = pembetulan.group(1).strip() if pembetulan else ""
    
    data["No"] = no_val
    data["Nomor Bukti Potong"] = no_val
    data["Masa Pajak"] = masa_val
    data["Sifat"] = sifat_val
    data["Pembetulan"] = pembetulan_val

    # --- IDENTITAS PENERIMA ---
    data["NPWP/NIK Penerima"] = get_value(text, r"A\.1\s+NPWP\s*/\s*NIK")
    data["Nama Penerima"] = get_value(text, r"A\.2\s+NAMA")
    data["Nitku Penerima"] = get_value(text, r"A\.3\s+NOMOR IDENTITAS")

    # --- PAJAK ---
    data["Jenis Fasilitas"] = get_value(text, r"B\.1\s+JENIS FASILITAS")
    data["Jenis PPh"] = get_value(text, r"B\.2\s+JENIS PPH")

    # --- OBJEK PAJAK ---
    pajak = re.search(
        r"(\d{2}-\d{3}-\d{2})\s+(.+?)\s+(\d+(?:\.\d{3})*)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d{3})*)",
        text,
        re.DOTALL
    )
    if pajak:
        data["Kode Objek Pajak"] = pajak.group(1)
        data["Objek Pajak"] = pajak.group(2).strip()
        data["Jumlah Penghasilan Bruto"] = convert_to_number(pajak.group(3))
        data["Tarif"] = float(pajak.group(4))
        data["PPh Dipotong"] = convert_to_number(pajak.group(5))
    else:
        data.update({
            "Kode Objek Pajak": "",
            "Objek Pajak": "",
            "Jumlah Penghasilan Bruto": None,
            "Tarif": None,
            "PPh Dipotong": None
        })

    # --- DOKUMEN ---
    data["Jenis Dokumen"] = get_jenis_dokumen(text)
    data["Nomor Dokumen"] = get_value(text, r"B\.9\s+NOMOR DOKUMEN")

    # --- PEMOTONG ---
    data["Npwp Pemotong"] = get_value(text, r"C\.1\s+NPWP\s*/\s*NIK")
    data["Nitku Pemotong"] = get_value(text, r"C\.2\s+NOMOR IDENTITAS TEMPAT KEGIATAN")
    data["Nama Pemotong"] = get_value(text, r"C\.3\s+NAMA PEMOTONG DAN/ATAU PEMUNGUT")

    # --- TANGGAL ---
    tanggal_doc = get_value(text, r"B\.8.*Tanggal")
    data["Tanggal Dokumen"] = tanggal_doc

    tanggal_bp = get_value(text, r"C\.4\s+TANGGAL")
    data["Tanggal Bukti Potong"] = tanggal_bp

    if tanggal_bp:
        tahun = re.search(r"\d{4}", tanggal_bp)
        data["Tahun Pajak"] = tahun.group(0) if tahun else ""
    else:
        data["Tahun Pajak"] = ""

    data["Nama Penandatangan"] = get_value(text, r"C\.5\s+NAMA PENANDATANGAN")

    return data


def extract_from_file(pdf_path: str) -> Dict:
    """Ekstrak data dari satu file PDF"""
    text = extract_text_from_pdf(pdf_path)
    return extract_data(text)
