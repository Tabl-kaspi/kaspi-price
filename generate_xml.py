import pandas as pd
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ССЫЛКА НА ВАШУ ОПУБЛИКОВАННУЮ GOOGLE ТАБЛИЦУ (В ФОРМАТЕ CSV)
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=csv"

def main():
    # Скачиваем актуальные данные из Google Таблицы
    df = pd.read_csv(GOOGLE_SHEET_URL)
    
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
    
    # Проходим по каждой строчке нашей таблицы (включая все новые товары)
    for index, row in df.iterrows():
        # Названия в скобках row['...'] должны СТРОГО совпадать с заголовками колонок в вашей таблице!
        offer = ET.SubElement(offers, 'offer', {'sku': str(row['Артикул'])})
        
        model = ET.SubElement(offer, 'model')
        model.text = str(row['Название товара'])
        
        brand = ET.SubElement(offer, 'brand')
        brand.text = str(row['Бренд'])
        
        price = ET.SubElement(offer, 'price')
        price.text = str(int(row['Цена']))
        
        availabilities = ET.SubElement(offer, 'availabilities')
        # Если товар доступен, ставим доставку/самовывоз доступными
        status = 'yes' if str(row['Доступность']).lower() in ['yes', 'да', '1'] else 'no'
        ET.SubElement(availabilities, 'availability', {'available': status, 'storeId': 'PP1'})

    # Форматируем XML в красивый вид
    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    # Записываем готовый прайс-лист в файл
    with open("price.xml", "wb") as f:
        f.write(pretty_xml)
        
    print("Прайс-лист успешно обновлен и включает новые товары!")

if __name__ == "__main__":
    main()
