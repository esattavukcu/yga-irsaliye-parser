#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import csv
import json
from bs4 import BeautifulSoup
from pathlib import Path

class IrsaliyeParserV2:
    def __init__(self, html_folder_path):
        self.html_folder_path = Path(html_folder_path)
        self.parsed_data = []
    
    def extract_text_from_cell(self, element):
        """HTML elementinden temiz metin çıkarır"""
        if element is None:
            return ""
        return element.get_text(strip=True)
    
    def parse_single_html(self, html_file_path):
        """Tek bir HTML dosyasını parse eder"""
        try:
            # Farklı encoding'leri dene
            encodings = ['utf-16', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
            content = ""
            
            for encoding in encodings:
                try:
                    with open(html_file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    break  # Başarılı okuma
                except UnicodeDecodeError:
                    continue
            
            if not content:
                print(f"Uyarı: {html_file_path.name} dosyası hiçbir encoding ile okunamadı")
                return
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # İrsaliye verileri
            irsaliye_data = {
                'dosya_adi': html_file_path.name,
                'irsaliye_no': '',
                'irsaliye_tarihi': '',
                'sevk_adresi': '',
                'sevk_edilen_kisi': '',
                'sevk_edilen_tel': '',
                'malzeme_kodu': '',
                'malzeme_aciklama': '',
                'adeti': '',
                'not_bilgileri': ''
            }
            
            # QR code div içindeki JSON veriyi bul
            qr_div = soup.find('div', id='qrvalue')
            if qr_div and qr_div.get_text(strip=True):
                try:
                    json_text = qr_div.get_text(strip=True)
                    qr_data = json.loads(json_text)
                    
                    # JSON'dan temel bilgileri al
                    irsaliye_data['irsaliye_no'] = qr_data.get('no', '')
                    irsaliye_data['irsaliye_tarihi'] = qr_data.get('tarih', '')
                    
                    # JSON'dan temel bilgiler başarıyla alındı
                    
                except json.JSONDecodeError as e:
                    print(f"JSON parse hatası: {e}")
            
            # Sevk edilen kişi bilgisini bul (customerPartyTable'dan)
            customer_table = soup.find('table', id='customerPartyTable')
            if customer_table:
                # "SAYIN" sonrası kısmı bul
                sayin_found = False
                for row in customer_table.find_all('tr'):
                    cell_text = self.extract_text_from_cell(row.find('td'))
                    if 'SAYIN' in cell_text:
                        sayin_found = True
                        continue
                    
                    # SAYIN'dan sonraki satırda isim var
                    if sayin_found and cell_text and cell_text.strip():
                        # HTML etiketlerini temizle ve ismi al
                        clean_text = cell_text.strip()
                        if clean_text and len(clean_text) > 2:  # Çok kısa metinleri atla
                            irsaliye_data['sevk_edilen_kisi'] = clean_text
                            break
            
            # Sevk Adresi'ni bul
            sevk_adresi_pattern = r'Sevk Adresi:(.*?)</span>'
            match = re.search(sevk_adresi_pattern, content)
            if match:
                sevk_adresi_raw = match.group(1).strip()
                # HTML etiketlerini temizle
                sevk_adresi_clean = BeautifulSoup(sevk_adresi_raw, 'html.parser').get_text(strip=True)
                
                # Telefon numarasını ayır
                tel_pattern = r'Tel:(\d+)'
                tel_match = re.search(tel_pattern, sevk_adresi_clean)
                if tel_match:
                    irsaliye_data['sevk_edilen_tel'] = tel_match.group(1)
                    # Telefon numarasını adresten çıkar
                    irsaliye_data['sevk_adresi'] = re.sub(r'\s*Tel:\d+', '', sevk_adresi_clean).strip()
                else:
                    irsaliye_data['sevk_adresi'] = sevk_adresi_clean
            
            # Malzeme tablosunu bul ve parse et
            tables = soup.find_all('table')
            malzeme_bulundu = False
            
            for table in tables:
                # Malzeme tablosunu tanımla (Malzeme Kodu başlığı olan tablo)
                headers = table.find_all('th') or table.find_all('td')
                header_texts = [self.extract_text_from_cell(th) for th in headers]
                
                if any('Malzeme Kodu' in header for header in header_texts):
                    # Bu malzeme tablosu
                    rows = table.find_all('tr')[1:]  # İlk satır başlık
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 3:
                            malzeme_kodu = self.extract_text_from_cell(cells[1])  # 2. sütun
                            malzeme_aciklama = self.extract_text_from_cell(cells[2])  # 3. sütun
                            miktar_cell = self.extract_text_from_cell(cells[3]) if len(cells) > 3 else ""  # 4. sütun
                            
                            # Miktarı temizle (sadece sayıları al)
                            miktar_match = re.search(r'(\d+)', miktar_cell)
                            miktar = miktar_match.group(1) if miktar_match else ""
                            
                            if malzeme_kodu:  # Boş satırları atla
                                irsaliye_entry = irsaliye_data.copy()
                                irsaliye_entry['malzeme_kodu'] = malzeme_kodu
                                irsaliye_entry['malzeme_aciklama'] = malzeme_aciklama
                                irsaliye_entry['adeti'] = miktar
                                self.parsed_data.append(irsaliye_entry)
                                malzeme_bulundu = True
            
            # Açıklamalar tablosunu bul
            for table in tables:
                headers = table.find_all('th')
                if any('Açıklamalar' in self.extract_text_from_cell(th) for th in headers):
                    rows = table.find_all('tr')[1:]  # İlk satır başlık
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            not_label = self.extract_text_from_cell(cells[0])
                            not_content = self.extract_text_from_cell(cells[1])
                            if 'Not:' in not_label and not_content:
                                # Bu not bilgisini tüm malzeme satırlarına ekle
                                for entry in self.parsed_data:
                                    if entry['dosya_adi'] == html_file_path.name:
                                        entry['not_bilgileri'] = not_content
            
            # Eğer malzeme bulunamadıysa, en azından temel bilgileri kaydet
            if not malzeme_bulundu:
                self.parsed_data.append(irsaliye_data)
                
        except Exception as e:
            print(f"Hata: {html_file_path.name} dosyası işlenirken hata oluştu: {str(e)}")
    
    def parse_all_html_files(self):
        """Klasördeki tüm HTML dosyalarını parse eder"""
        html_files = list(self.html_folder_path.glob("*.html"))
        
        print(f"{len(html_files)} HTML dosyası bulundu...")
        
        for i, html_file in enumerate(html_files, 1):
            print(f"İşleniyor: {html_file.name} ({i}/{len(html_files)})")
            self.parse_single_html(html_file)
        
        print(f"Toplam {len(self.parsed_data)} kayıt çıkarıldı.")
    
    def save_to_csv(self, output_file):
        """Verileri CSV formatında kaydeder"""
        if not self.parsed_data:
            print("Kaydedilecek veri bulunamadı!")
            return
        
        fieldnames = [
            'dosya_adi', 'irsaliye_no', 'irsaliye_tarihi', 'sevk_adresi', 
            'sevk_edilen_kisi', 'sevk_edilen_tel', 'malzeme_kodu', 'malzeme_aciklama', 'adeti', 'not_bilgileri'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in self.parsed_data:
                writer.writerow(row)
        
        print(f"Veriler {output_file} dosyasına kaydedildi.")
    
    def save_to_json(self, output_file):
        """Verileri JSON formatında kaydeder"""
        if not self.parsed_data:
            print("Kaydedilecek veri bulunamadı!")
            return
        
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.parsed_data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"Veriler {output_file} dosyasına kaydedildi.")
    
    def print_summary(self):
        """Parse edilen verilerin özetini gösterir"""
        if not self.parsed_data:
            print("Parse edilen veri bulunamadı!")
            return
        
        print("\n=== İRSALİYE VERİLERİ ÖZETİ ===")
        print(f"Toplam kayıt sayısı: {len(self.parsed_data)}")
        
        # Benzersiz irsaliye sayısı
        unique_invoices = len(set(entry['irsaliye_no'] for entry in self.parsed_data if entry['irsaliye_no']))
        print(f"Benzersiz irsaliye sayısı: {unique_invoices}")
        
        # İlk 5 kaydı göster
        print("\nİlk 5 kayıt:")
        for i, entry in enumerate(self.parsed_data[:5], 1):
            print(f"{i}. {entry['irsaliye_no']} ({entry['irsaliye_tarihi']}) - {entry['malzeme_kodu']} - {entry['adeti']} adet")

def main():
    # HTML dosyalarının bulunduğu klasör
    html_folder = "/Users/esat/Desktop/Yga İrsaliyeler"
    
    # Parser'ı başlat
    parser = IrsaliyeParserV2(html_folder)
    
    # Tüm HTML dosyalarını parse et
    parser.parse_all_html_files()
    
    # Özet bilgileri göster
    parser.print_summary()
    
    # Verileri kaydet
    output_folder = "/Users/esat/yga_html_parser"
    parser.save_to_csv(f"{output_folder}/irsaliye_verileri_final.csv")
    parser.save_to_json(f"{output_folder}/irsaliye_verileri_final.json")

if __name__ == "__main__":
    main()