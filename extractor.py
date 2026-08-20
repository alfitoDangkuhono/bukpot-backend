import pdfplumber
import re
from typing import Dict, Optional
from functools import lru_cache

# Pre-compiled regex patterns for better performance
REGEX_PATTERNS = {
    "nomor": re.compile(r"([0-9A-Z]{8})\s+(\d{2}-\d{4})"),
    "nomor_simple": re.compile(r"([0-9A-Z]{8})"),
    "masa": re.compile(r"(\d{2}-\d{4})"),
    "sifat": re.compile(r"(TIDAK\s+FINAL|FINAL)", re.IGNORECASE),
    "pembetulan": re.compile(r"(NORMAL|PEMBETULAN|DIBATALKAN)", re.IGNORECASE),
    "jenis_dokumen": re.compile(
        r"B\.8\s+DOKUMEN DASAR BUKTI JENIS DOKUMEN\s*:\s*(.+?)\s+Tanggal",
        re.IGNORECASE
    ),
    "pajak": re.compile(
        r"(\d{2}-\d{3}-\d{2})\s+(.+?)\s+(\d+(?:\.\d{3})*)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d{3})*)",
        re.DOTALL
    ),
    "tahun": re.compile(r"\d{4}")
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """Ekstrak text dari PDF dengan layout preservation"""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def convert_to_number(text_value: Optional[str]) -> Optional[float]:
    """Konversi text dengan format Indonesia (titik pemisah ribuan) ke number"""
    if not text_value or not isinstance(text_value, str):
        return None
    try:
        # Contoh: "1.234.567" -> "1234567" -> 1234567
        num_str = text_value.replace(".", "").strip()
        return float(num_str) if num_str else None
    except (ValueError, AttributeError):
        return None


def get_value(text: str, label_regex: str) -> str:
    """Ekstrak nilai dari text menggunakan regex pattern"""
    pattern = rf"{label_regex}\s*[:：]\s*(.+?)(?=\n|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def get_jenis_dokumen(text: str) -> str:
    """Ekstrak jenis dokumen"""
    match = REGEX_PATTERNS["jenis_dokumen"].search(text)
    return match.group(1).strip() if match else ""


def extract_data(text: str) -> Dict:
    """Ekstrak semua data dari text PDF"""
    data = {}

    # --- HEADER ---
    nomor_match = REGEX_PATTERNS["nomor"].search(text)
    
    if nomor_match:
        no_val = nomor_match.group(1)
        masa_val = nomor_match.group(2)
    else:
        # Fallback untuk format yang berbeda
        no_match = REGEX_PATTERNS["nomor_simple"].search(text)
        no_val = no_match.group(1) if no_match else ""
        
        masa_match = REGEX_PATTERNS["masa"].search(text)
        masa_val = masa_match.group(1) if masa_match else ""
    
    # Cari sifat
    sifat_match = REGEX_PATTERNS["sifat"].search(text)
    sifat_val = sifat_match.group(1).strip() if sifat_match else ""
    
    # Cari pembetulan
    pembetulan_match = REGEX_PATTERNS["pembetulan"].search(text)
    pembetulan_val = pembetulan_match.group(1).strip() if pembetulan_match else ""
    
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
    pajak_match = REGEX_PATTERNS["pajak"].search(text)
    if pajak_match:
        data["Kode Objek Pajak"] = pajak_match.group(1)
        data["Objek Pajak"] = pajak_match.group(2).strip()
        data["Jumlah Penghasilan Bruto"] = convert_to_number(pajak_match.group(3))
        data["Tarif"] = float(pajak_match.group(4))
        data["PPh Dipotong"] = convert_to_number(pajak_match.group(5))
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
        tahun_match = REGEX_PATTERNS["tahun"].search(tanggal_bp)
        data["Tahun Pajak"] = tahun_match.group(0) if tahun_match else ""
    else:
        data["Tahun Pajak"] = ""

    data["Nama Penandatangan"] = get_value(text, r"C\.5\s+NAMA PENANDATANGAN")

    return data


def extract_from_file(pdf_path: str) -> Dict:
    """Ekstrak data dari satu file PDF"""
    text = extract_text_from_pdf(pdf_path)
    return extract_data(text)
