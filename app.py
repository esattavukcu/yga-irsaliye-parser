#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import csv
import json
import io
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import zipfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'yga_irsaliye_parser_secret_key_2025'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'html', 'zip'}

# Klasörleri oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class IrsaliyeParserWeb:
    def __init__(self):
        self.parsed_data = []
    
    def extract_text_from_cell(self, element):
        """HTML elementinden temiz metin çıkarır"""
        if element is None:
            return ""
        return element.get_text(strip=True)
    
    def parse_html_content(self, content, filename):
        """HTML içeriğini parse eder"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # İrsaliye verileri
            irsaliye_data = {
                'dosya_adi': filename,
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
                                    if entry['dosya_adi'] == filename:
                                        entry['not_bilgileri'] = not_content
            
            # Eğer malzeme bulunamadıysa, en azından temel bilgileri kaydet
            if not malzeme_bulundu:
                self.parsed_data.append(irsaliye_data)
                
        except Exception as e:
            print(f"Hata: {filename} dosyası işlenirken hata oluştu: {str(e)}")
            return False
        
        return True
    
    def parse_single_html_file(self, file_path_or_content, filename):
        """Tek bir HTML dosyasını parse eder"""
        try:
            if isinstance(file_path_or_content, str) and os.path.isfile(file_path_or_content):
                # Dosya yolu verildi
                encodings = ['utf-16', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
                content = ""
                
                for encoding in encodings:
                    try:
                        with open(file_path_or_content, 'r', encoding=encoding) as file:
                            content = file.read()
                        break  # Başarılı okuma
                    except UnicodeDecodeError:
                        continue
                
                if not content:
                    return False
            else:
                # İçerik direkt verildi
                content = file_path_or_content
            
            return self.parse_html_content(content, filename)
            
        except Exception as e:
            print(f"Hata: {filename} dosyası işlenirken hata oluştu: {str(e)}")
            return False
    
    def get_parsed_data(self):
        return self.parsed_data
    
    def clear_data(self):
        self.parsed_data = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('Dosya seçilmedi!')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        flash('Dosya seçilmedi!')
        return redirect(request.url)
    
    parser = IrsaliyeParserWeb()
    processed_count = 0
    total_count = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            if filename.endswith('.zip'):
                # ZIP dosyasını işle
                try:
                    with zipfile.ZipFile(file, 'r') as zip_ref:
                        for zip_info in zip_ref.infolist():
                            if zip_info.filename.endswith('.html'):
                                total_count += 1
                                try:
                                    html_content = zip_ref.read(zip_info).decode('utf-8')
                                    if parser.parse_single_html_file(html_content, zip_info.filename):
                                        processed_count += 1
                                except:
                                    # UTF-8 başarısız, diğer encodingleri dene
                                    encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
                                    for encoding in encodings:
                                        try:
                                            html_content = zip_ref.read(zip_info).decode(encoding)
                                            if parser.parse_single_html_file(html_content, zip_info.filename):
                                                processed_count += 1
                                            break
                                        except:
                                            continue
                except Exception as e:
                    flash(f'ZIP dosyası işlenirken hata: {str(e)}')
                    
            elif filename.endswith('.html'):
                # Tek HTML dosyasını işle
                total_count += 1
                try:
                    html_content = file.read().decode('utf-8')
                    if parser.parse_single_html_file(html_content, filename):
                        processed_count += 1
                except:
                    # UTF-8 başarısız, diğer encodingleri dene
                    file.seek(0)  # Dosya pointerını başa al
                    encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
                    for encoding in encodings:
                        try:
                            file.seek(0)
                            html_content = file.read().decode(encoding)
                            if parser.parse_single_html_file(html_content, filename):
                                processed_count += 1
                            break
                        except:
                            continue
    
    # Sonuçları kaydet
    parsed_data = parser.get_parsed_data()
    
    if parsed_data:
        # CSV oluştur
        csv_path = os.path.join(RESULTS_FOLDER, 'irsaliye_verileri.csv')
        fieldnames = [
            'dosya_adi', 'irsaliye_no', 'irsaliye_tarihi', 'sevk_adresi', 
            'sevk_edilen_kisi', 'sevk_edilen_tel', 'malzeme_kodu', 'malzeme_aciklama', 'adeti', 'not_bilgileri'
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in parsed_data:
                writer.writerow(row)
        
        # JSON oluştur
        json_path = os.path.join(RESULTS_FOLDER, 'irsaliye_verileri.json')
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(parsed_data, jsonfile, ensure_ascii=False, indent=2)
        
        flash(f'Başarıyla işlendi! {processed_count}/{total_count} dosya parse edildi. {len(parsed_data)} kayıt oluşturuldu.')
        return render_template('results.html', 
                             data=parsed_data[:50],  # İlk 50 kaydı göster
                             total_records=len(parsed_data),
                             processed_files=processed_count,
                             total_files=total_count)
    else:
        flash('Hiçbir veri çıkarılamadı!')
        return redirect(url_for('index'))

@app.route('/download/<file_type>')
def download_file(file_type):
    if file_type == 'csv':
        file_path = os.path.join(RESULTS_FOLDER, 'irsaliye_verileri.csv')
        mimetype = 'text/csv'
    elif file_type == 'json':
        file_path = os.path.join(RESULTS_FOLDER, 'irsaliye_verileri.json')
        mimetype = 'application/json'
    else:
        flash('Geçersiz dosya türü!')
        return redirect(url_for('index'))
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, mimetype=mimetype)
    else:
        flash('Dosya bulunamadı!')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)