import pandas as pd
import requests
import io
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ==========================================
# НАСТРОЙКИ И КОНСТАНТЫ
# ==========================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=xlsx"
MERCHANT_ID = "30179693"  # Ваш ID партнера из Kaspi Pay

def clean_text(text):
    if pd.isna(text):
        return ""
    text_str = str(text).strip()
    text_str = text_str.replace("&", " и ").replace("<", " ").replace(">", " ")
    return text_str

def main():
    print("Начало скачивания таблицы...")
    response = requests.get(GOOGLE_SHEET_URL)
    if response.status_code != 200:
        print(f"Ошибка скачивания таблицы! Код: {response.status_code}")
        return

    df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    print("Таблица Excel успешно прочитана!")
    
    current_date = time.strftime("%d-%m-%Y %H:%M:%S")
    
    # Очищенный корневой элемент по самым последним правилам валидации Kaspi
    kaspi_catalog = ET.Element('kaspi_catalog', {
        'date': current_date,
        'xmlns': 'kaspiShopping',
        'xmlns:xsi': 'http://w3.org'
    })
    
    company = ET.SubElement(kaspi_catalog, 'company')
    company.text = "Tabl-kaspi"
    
    merchant_id_elem = ET.SubElement(kaspi_catalog, 'merchantid')
    merchant_id_elem.text = MERCHANT_ID
    
    offers = ET.SubElement(kaspi_catalog, 'offers')
    stores = ['PP1', 'PP2', 'PP3', 'PP4', 'PP5']
    
    for index, row in df.iterrows():
        if 'SKU' not in df.columns or pd.isna(row['SKU']):
            continue
        
        sku_str = str(row['SKU']).strip().split('.')[0]
        if sku_str.lower() in ['sku', 'параметр', '']:
            continue
            
        if 'price' not in df.columns or pd.isna(row['price']) or str(row['price']).strip() == '':
            continue
            
        offer = ET.SubElement(offers, 'offer', {'sku': sku_str})
        
        model = ET.SubElement(offer, 'model')
        model.text = clean_text(row.get('model', 'Без названия'))
        
        brand = ET.SubElement(offer, 'brand')
        brand.text = clean_text(row.get('brand', 'Без бренда'))
        
        availabilities = ET.SubElement(offer, 'availabilities')
        
        for store in stores:
            if store in df.columns:
                val_str = str(row[store]).strip().split('.')[0]
                
                is_numeric_stock = val_str.isdigit() and int(val_str) > 0
                
                if val_str.lower() in ['yes', 'да', 'true'] or is_numeric_stock:
                    status = 'yes'
                    count = val_str if val_str.isdigit() else "100"
                else:
                    status = 'no'
                    count = "0"
                
                preorder_days = ""
                if 'preorder' in df.columns and not pd.isna(row['preorder']):
                    try:
                        preorder_days = str(row['preorder']).strip().split('.')[0]
                    except:
                        pass
                
                avail_attrs = {'available': status, 'storeId': store}
                if status == 'yes' and preorder_days != "" and preorder_days != "0":
                    avail_attrs['preOrder'] = preorder_days
                    
                availability_elem = ET.SubElement(availabilities, 'availability', avail_attrs)
                availability_elem.text = count
                
        price = ET.SubElement(offer, 'price')
        try:
            price_clean = str(row['price']).strip().replace(' ', '').split('.')[0]
            price.text = str(int(price_clean))
        except:
            price.text = str(row['price']).strip()

    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    with open("price.xml", "wb") as f:
        f.write(pretty_xml)
        
    print("Файл price.xml успешно перегенерирован без xsi:schemaLocation!")

if __name__ == "__main__":
    main()
