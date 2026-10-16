import pandas as pd
import requests
import io
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ССЫЛКА НА ВАШУ GOOGLE ТАБЛИЦУ (ОБЯЗАТЕЛЬНО С output=xlsx НА КОНЦЕ)
GOOGLE_SHEET_URL = "ВСТАВЬТЕ_СЮДА_ВАШУ_ССЫЛКУ"

def main():
    print("https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=xlsx")
    
    # Скачиваем файл как бинарный поток данных
    response = requests.get(GOOGLE_SHEET_URL)
    
    if response.status_code != 200:
        print(f"Ошибка скачивания таблицы! Код ответа: {response.status_code}")
        return

    # Читаем данные строго как Excel (.xlsx) из оперативной памяти
    df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    print("Таблица успешно прочитана в формате Excel!")
    
    # Создаем корневой элемент XML для Kaspi
    kaspi_catalog = ET.Element('kaspi_catalog', {
        'date': 'string',
        'xmlns': 'http://chorny.ru',
        'xmlns:xsi': 'http://w3.org',
        'xsi:schemaLocation': 'http://chorny.ru kaspi_catalog.xsd'
    })
    
    company = ET.SubElement(kaspi_catalog, 'company')
    company.text = "Ваша Компания"
    
    offers = ET.SubElement(kaspi_catalog, 'offers')
    
    # Проходим по каждой строчке таблицы
    for index, row in df.iterrows():
        # Защита от пустых строк в конце файла
        if pd.isna(row['Артикул']) or pd.isna(row['Цена']):
            continue
            
        offer = ET.SubElement(offers, 'offer', {'sku': str(row['Артикул'])})
        
        model = ET.SubElement(offer, 'model')
        model.text = str(row['Название товара'])
        
        brand = ET.SubElement(offer, 'brand')
        brand.text = str(row['Бренд'])
        
        price = ET.SubElement(offer, 'price')
        price.text = str(int(row['Цена']))
        
        availabilities = ET.SubElement(offer, 'availabilities')
        
        # Проверяем доступность (работает с "yes", "да", 1 или просто если колонка заполнена)
        avail_str = str(row['Доступность']).lower().strip()
        status = 'yes' if avail_str in ['yes', 'да', '1', 'true'] else 'no'
        
        ET.SubElement(availabilities, 'availability', {'available': status, 'storeId': 'PP1'})

    # Форматируем XML в красивый вид
    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    # Записываем готовый прайс-лист
    with open("price.xml", "wb") as f:
        f.write(pretty_xml)
        
    print("Файл price.xml успешно сгенерирован и включает все новые товары!")

if __name__ == "__main__":
    main()
