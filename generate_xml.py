import pandas as pd
import requests
import io
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Ваша ссылка на Google Таблицу в формате TSV (output=tsv)
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=xlsx"
MERCHANT_ID = "30179693"  # Ваш ID партнера из Kaspi Pay

def main():
    print("Начало скачивания таблицы...")
    response = requests.get(GOOGLE_SHEET_URL)
    if response.status_code != 200:
        print(f"Ошибка скачивания таблицы! Код ответа: {response.status_code}")
        return

    # Читаем данные из оперативной памяти как Excel-файл
    df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    print("Таблица Excel успешно прочитана!")
    
    # Текущая дата и время для заголовка прайса
    current_date = time.strftime("%d-%m-%Y %H:%M:%S")
    
    # Создаем корневой элемент XML СТРОГО по официальным стандартам Kaspi
    kaspi_catalog = ET.Element('kaspi_catalog', {
        'date': current_date,
        'xmlns': 'kaspiShopping',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'kaspiShopping http://kaspi.kz/kaspishopping.xsd'
    })
    
    # Обязательные поля шапки прайса в правильном порядке регистров (маленькие буквы)
    company = ET.SubElement(kaspi_catalog, 'company')
    company.text = "Tabl-kaspi"
    
    merchant_id_elem = ET.SubElement(kaspi_catalog, 'merchantid')
    merchant_id_elem.text = MERCHANT_ID
    
    offers = ET.SubElement(kaspi_catalog, 'offers')
    stores = ['PP1', 'PP2', 'PP3', 'PP4', 'PP5']
    
    for index, row in df.iterrows():
        # Безопасное чтение SKU с защитой от пустых строк
        if 'SKU' not in df.columns or pd.isna(row['SKU']):
            continue
        sku_str = str(row['SKU']).strip()
        if sku_str.lower() in ['sku', 'параметр', '']:
            continue
            
        if 'price' not in df.columns or pd.isna(row['price']) or str(row['price']).strip() == '':
            continue
            
        offer = ET.SubElement(offers, 'offer', {'sku': sku_str})
        
        model = ET.SubElement(offer, 'model')
        model.text = str(row['model']).strip() if 'model' in df.columns and not pd.isna(row['model']) else "Без названия"
        
        brand = ET.SubElement(offer, 'brand')
        brand.text = str(row['brand']).strip() if 'brand' in df.columns and not pd.isna(row['brand']) else "Без бренда"
        
        availabilities = ET.SubElement(offer, 'availabilities')
        
        for store in stores:
            if store in df.columns:
                val = str(row[store]).lower().strip()
                status = 'yes' if val in ['yes', 'да', '1', '1.0', 'true'] else 'no'
                
                preorder_days = ""
                if 'preorder' in df.columns and not pd.isna(row['preorder']):
                    try:
                        preorder_days = str(int(float(str(row['preorder']))))
                    except:
                        pass
                
                # Формируем структуру склада с учетом дней предзаказа по требованиям Kaspi
                avail_attrs = {'available': status, 'storeId': store}
                if status == 'yes' and preorder_days != "":
                    avail_attrs['preOrder'] = preorder_days  # Специфичный регистр Kaspi XSD
                    
                ET.SubElement(availabilities, 'availability', avail_attrs)
                
        price = ET.SubElement(offer, 'price')
        try:
            price.text = str(int(float(str(row['price']).replace(' ', ''))))
        except:
            price.text = str(row['price']).strip()

    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    with open("price.xml", "wb") as f:
        f.write(pretty_xml)
        
    print("Файл price.xml успешно перегенерирован с правильными пространствами имен!")

if __name__ == "__main__":
    main()
