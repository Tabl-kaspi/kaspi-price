import pandas as pd
import requests
import io
import xml.etree.ElementTree as ET
from xml.dom import minidom

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=xlsx"
MERCHANT_ID = "30179693"  # Ваш ID партнера из Kaspi Pay

def main():
    print("Начало скачивания таблицы...")
    response = requests.get(GOOGLE_SHEET_URL)
    if response.status_code != 200:
        print(f"Ошибка скачивания таблицы! Код ответа: {response.status_code}")
        return

    df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    print("Таблица успешно прочитана в формате Excel!")
    
    # Создаем корневой элемент XML по строгим стандартам новой XSD Kaspi
    kaspi_catalog = ET.Element('kaspi_catalog', {
        'date': 'string',
        'xmlns': 'http://chorny.ru',
        'xmlns:xsi': 'http://w3.org',
        'xsi:schemaLocation': 'http://chorny.ru kaspi_catalog.xsd'
    })
    
    # Обязательные поля шапки прайса в правильном порядке
    company = ET.SubElement(kaspi_catalog, 'company')
    company.text = "Ваша Компания"
    
    merchant_id_elem = ET.SubElement(kaspi_catalog, 'merchantId')
    merchant_id_elem.text = MERCHANT_ID
    
    offers = ET.SubElement(kaspi_catalog, 'offers')
    stores = ['PP1', 'PP2', 'PP3', 'PP4', 'PP5']
    
    for index, row in df.iterrows():
        if pd.isna(row['SKU']) or str(row['SKU']).strip().lower() in ['sku', 'параметр', '']:
            continue
        if pd.isna(row['price']) or str(row['price']).strip() == '':
            continue
            
        offer = ET.SubElement(offers, 'offer', {'sku': str(row['SKU']).split('.')[0]})
        
        model = ET.SubElement(offer, 'model')
        model.text = str(row['model']) if not pd.isna(row['model']) else "Без названия"
        
        brand = ET.SubElement(offer, 'brand')
        brand.text = str(row['brand']) if not pd.isna(row['brand']) else "Без бренда"
        
        price = ET.SubElement(offer, 'price')
        try:
            price.text = str(int(float(row['price'])))
        except:
            price.text = str(row['price'])
        
        availabilities = ET.SubElement(offer, 'availabilities')
        
        for store in stores:
            if store in df.columns:
                val = str(row[store]).lower().strip()
                status = 'yes' if val in ['yes', 'да', '1', '1.0', 'true'] else 'no'
                
                # Дополнительно считываем колонку предзаказа J (preorder)
                preorder_days = ""
                if 'preorder' in df.columns and not pd.isna(row['preorder']):
                    preorder_days = str(int(float(row['preorder'])))
                
                # Формируем структуру склада с учетом дней предзаказа
                avail_attrs = {'available': status, 'storeId': store}
                if status == 'yes' and preorder_days != "":
                    avail_attrs['preorder'] = preorder_days
                    
                ET.SubElement(availabilities, 'availability', avail_attrs)

    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    with open("price.xml", "wb") as f:
        f.write(pretty_xml)
        
    print("Файл price.xml успешно перегенерирован с MERCHANT_ID!")

if __name__ == "__main__":
    main()
