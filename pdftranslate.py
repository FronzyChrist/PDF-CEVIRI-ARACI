#!/usr/bin/env python3
import os
import json
import time
import io
import argparse
import fitz  
import pytesseract
from fpdf import FPDF
from PIL import Image
from PyPDF2 import PdfMerger
import argostranslate.package
import argostranslate.translate


CONFIG = {
    "input_pdf": "input.pdf",
    "output_dir": "translated_pages",
    "output_pdf": "output_translated.pdf", 
    "progress_file": "progress.json",
    "font_path": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "tesseract_path": "/opt/homebrew/bin/tesseract",
    "source_lang": "en",
    "target_lang": "tr",
    "ocr_dpi": 200
}

class PDFTranslator:
    def __init__(self, config):
        self.config = config
        self.setup_directories()
        self.setup_tesseract()
        self.setup_translation_model()
        
    def setup_directories(self):
        os.makedirs(self.config["output_dir"], exist_ok=True)
        print("Çıktı dizini hazırlandı")
        
    def setup_tesseract(self):
        pytesseract.pytesseract.tesseract_cmd = self.config["tesseract_path"]
        
    def setup_translation_model(self):
        
        print("Çeviri modeli yükleniyor...")
        
        langs = argostranslate.translate.load_installed_languages()
        from_lang = next((l for l in langs if l.code == self.config["source_lang"]), None)
        to_lang = next((l for l in langs if l.code == self.config["target_lang"]), None)
        
        if not from_lang or not to_lang:
            raise RuntimeError("Çeviri modeli bulunamadı! Lütfen önce yükleyin.")
            
        self.translation = from_lang.get_translation(to_lang)
        print("Çeviri modeli hazır: English → Turkish")
    
    def load_progress(self):
       
        if os.path.exists(self.config["progress_file"]):
            with open(self.config["progress_file"], "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_page", 1)
        return 1
    
    def save_progress(self, page_num):
        progress_data = {"last_page": page_num}
        with open(self.config["progress_file"], "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def extract_text_from_page(self, page):
        text = page.get_text("text").strip()
        if text:
            return text
            
       
        print("OCR ile metin çıkarılıyor...")
        pix = page.get_pixmap(dpi=self.config["ocr_dpi"])
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        return pytesseract.image_to_string(img, lang="eng").strip()
    
    def create_translated_pdf(self, page_num, text):
        pdf = FPDF()
        pdf.add_page()
        
       
        try:
            pdf.add_font("ArialUnicode", "", self.config["font_path"])
            pdf.set_font("ArialUnicode", size=12)
        except:
            print("Özel yazı tipi yüklenemedi, varsayılan kullanılıyor")
            pdf.set_font("Arial", size=12)
        
        
        pdf.multi_cell(0, 10, text)
        
        
        output_path = os.path.join(self.config["output_dir"], f"page_{page_num:03d}.pdf")
        pdf.output(output_path)
        return output_path
    
    def merge_pdfs(self):
        print("\nPDF sayfaları birleştiriliyor...")
        
        merger = PdfMerger()
        doc = fitz.open(self.config["input_pdf"])
        
        for i in range(1, len(doc) + 1):
            part_path = os.path.join(self.config["output_dir"], f"page_{i:03d}.pdf")
            if os.path.exists(part_path):
                merger.append(part_path)
                print(f"Sayfa {i} eklendi")
        
        merger.write(self.config["output_pdf"])
        merger.close()
        print(f"Tüm sayfalar birleştirildi: {self.config['output_pdf']}")
    
    def translate_pdf(self):
        print(f"PDF çevirisi başlatılıyor: {self.config['input_pdf']}")
        
       
        doc = fitz.open(self.config["input_pdf"])
        total_pages = len(doc)
        start_page = self.load_progress()
        
        print(f"Toplam sayfa: {total_pages}")
        print(f"Başlangıç sayfası: {start_page}")
        
        
        for page_num in range(start_page, total_pages + 1):
            print(f"\n--- Sayfa {page_num}/{total_pages} ---")
            
            try:
                page = doc[page_num - 1]
                
               
                original_text = self.extract_text_from_page(page)
                if not original_text:
                    print("Bu sayfada metin bulunamadı, boş sayfa oluşturuluyor")
                    original_text = "[BOŞ SAYFA]"
                
                
                print("Çeviri yapılıyor...")
                translated_text = self.translation.translate(original_text)
                
               
                output_path = self.create_translated_pdf(page_num, translated_text)
                print(f"Kaydedildi: {os.path.basename(output_path)}")
                
               
                self.save_progress(page_num)
                print(f"Sayfa {page_num} tamamlandı")
                
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Hata: {str(e)}")
                continue
        
        doc.close()
        
       
        self.merge_pdfs()
        
        print("\nÇeviri tamamlandı!")
        print(f"Çıktı: {self.config['output_pdf']}")

def main():
    print("=" * 50)
    print("    PDF ÇEVİRİ ARACI")
    print("    English → Turkish")
    print("=" * 50)
    
    try:
       
        translator = PDFTranslator(CONFIG)
        
      
        translator.translate_pdf()
        
    except Exception as e:
        print(f"\nProgram hatası: {str(e)}")
        print("Lütfen yapılandırmayı kontrol edin.")

if __name__ == "__main__":
    main()
