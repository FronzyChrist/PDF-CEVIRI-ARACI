import fitz 
import os, json, time
import pytesseract
from fpdf import 
from PIL import Image
import io
import argostranslate.package, argostranslate.translate
from PyPDF2 import PdfMerger


INPUT_PDF = "input.pdf"
OUTPUT_DIR = "translated_pages"
OUTPUT_PDF = "output_translated.pdf"
PROGRESS_FILE = "progress.json"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"


langs = argostranslate.translate.load_installed_languages()
from_lang = next((l for l in langs if l.code == "en"), None)
to_lang = next((l for l in langs if l.code == "tr"), None)
if not from_lang or not to_lang:
    raise RuntimeError("İngilizce → Türkçe modeli bulunamadı. Önce yükle!")

translation = from_lang.get_translation(to_lang)
print("✅ Çeviri modeli hazır: English → Turkish")


os.makedirs(OUTPUT_DIR, exist_ok=True)
start_page = 1
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        data = json.load(f)
        start_page = data.get("last_page", 1)

doc = fitz.open(INPUT_PDF)
print(f"📖 Kaldığın yerden devam ediliyor: Sayfa {start_page}")
print(f"Toplam {len(doc)} sayfa bulundu.")


def extract_text_with_ocr(page):
    text = page.get_text("text").strip()
    if text:
        return text
    pix = page.get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang="eng").strip()

def save_translated_page(page_num, text):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("ArialUnicode", "", FONT_PATH)
    pdf.set_font("ArialUnicode", size=12)
    pdf.multi_cell(0, 10, text)
    out_path = os.path.join(OUTPUT_DIR, f"page_{page_num}.pdf")
    pdf.output(out_path)
    print(f"💾 Sayfa {page_num} kaydedildi: {out_path}")

for i in range(start_page, len(doc) + 1):
    page = doc[i - 1]
    try:
        text = extract_text_with_ocr(page)
        if not text:
            print(f"⚠️ Sayfa {i}: metin bulunamadı.")
            continue
        translated = translation.translate(text)
        save_translated_page(i, translated)
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"last_page": i}, f)
        print(f"✅ Sayfa {i}/{len(doc)} çevrildi ve kaydedildi.")
    except Exception as e:
        print(f"❌ Sayfa {i} hata: {e}")
    time.sleep(0.05)


merger = PdfMerger()
for i in range(1, len(doc) + 1):
    part_path = os.path.join(OUTPUT_DIR, f"page_{i}.pdf")
    if os.path.exists(part_path):
        merger.append(part_path)
merger.write(OUTPUT_PDF)
merger.close()
print("🎉 Tüm sayfalar birleştirildi →", OUTPUT_PDF)