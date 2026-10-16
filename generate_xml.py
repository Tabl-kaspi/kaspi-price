import pandas as pd
import requests
import io
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Ваша реальная ссылка на Google Таблицу в формате Excel
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=xlsx"

def main():
    print("Начало скачивания таблицы...")
    
    response = requests.get(GOOGLE_SHEET_URL)
    if response.status_code != 200:
        print(f"Ошибка скачивания таблицы! Код ответа: {response.status_code}")
        return

    # Читаем данные строго как Excel (.xlsx) из оперативной памяти
    df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    print("Таблица успешно прочитана в формате Excel!")
    
    # Создаем корневой элемент XML для Kaspi с официальной схемой
    kaspi_catalog = ET.Element('kaspi_catalog', {
        'date': 'string',
        'xmlns': 'kaspiShopping',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'kaspiShopping http://kaspi.kz/kaspishopping.xsd'
    })

    
    company = ET.SubElement(kaspi_catalog, 'company')
    company.text = "Ваша Компания"
    
    offers = ET.SubElement(kaspi_catalog, 'offers')
    
    # Склады, которые есть в вашей таблице
    stores = ['PP1', 'PP2', 'PP3', 'PP4', 'PP5']
    
    # Проходим по каждой строчке таблицы
    for index, row in df.iterrows():
        # Защита от пустых строк и системных строк-описаний внизу таблицы
        if pd.isna(row['SKU']) or str(row['SKU']).strip().lower() in ['sku', 'параметр', '']:
            continue
        if pd.isna(row['price']) or str(row['price']).strip() == '':
            continue
            
        # Генерация элемента товара по его SKU
        offer = ET.SubElement(offers, 'offer', {'sku': str(row['SKU']).split('.')[0]})
        
        model = ET.SubElement(offer, 'model')
        model.text = str(row['model']) if not pd.isna(row['model']) else "Без названия"
        
        brand = ET.SubElement(offer, 'brand')
        brand.text = str(row['brand']) if not pd.isna(row['brand']) else "Без бренда"
        
        price = ET.SubElement(offer, 'price')
        # Превращаем цену в целое число, убирая возможные копейки после Excel (.0)
        try:
            price.text = str(int(float(row['price'])))
        except:
            price.text = str(row['price'])
        
        availabilities = ET.SubElement(offer, 'availabilities')
        
        # Перебираем все склады и проверяем их доступность из таблицы
        for store in stores:
            if store in df.columns:
                val = str(row[store]).lower().strip()
                # Товар доступен, если написано "yes", "да", "1", "1.0"
                if val in ['yes', 'да', '1', '1.0', 'true']:
                    status = 'yes'
                else:
                    status = 'no'
                
                ET.SubElement(availabilities, 'availability', {'available': status, 'storeId': store})

    # Форматируем XML в красивый структурированный вид
    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    # Записываем готовый прайс-лист для Kaspi
    with open("price.xml", "wb") as f:
        f.write(pretty_xml)
        
    print("Файл price.xml успешно обновлен, отфильтрован и включает все новые товары!")

if __name__ == "__main__":
    main()
