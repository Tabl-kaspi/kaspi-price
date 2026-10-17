import pandas as pd
import requests
import io
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ==========================================
# ВАШИ НАСТРОЙКИ И КОНСТАНТЫ
# ==========================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnieHgL-YpE6fxefPF6IAwfwhEbgEKg3vVk-b9_YTd573CxKcQXcDZXU1y0m_aiM_Wb4YKFZshkR1-/pub?output=xlsx"
MERCHANT_ID = "30179693"  # Ваш ID партнера из Kaspi Pay
KASPI_TOKEN = "BrSozK7M8/D4rWYwe6oIyVs4wmwmv7iLsdJqShKPQPk="  # Секретный токен авторизации

def upload_price_to_kaspi(file_path, token):
    """
    Принудительно загружает готовый XML-прайс в Kaspi через API,
    чтобы сократить время обновления остатков до пары минут.
    """
    url = "https://kaspi.kz"
    headers = {
        "X-Auth-Token": token,
        "Content-Type": "application/xml"
    }
    
    print("Отправка прайс-листа в API Kaspi...")
    try:
        with open(file_path, "rb") as f:
            response = requests.post(url, headers=headers, data=f)
            
        if response.status_code == 200 or response.status_code == 202:
            print("Успешно! Kaspi принял прайс-лист и обновит остатки на витрине в течение 2-5 минут.")
        else:
            print(f"Ошибка загрузки в Kaspi! Код ответа: {response.status_code}")
            print(f"Детали ошибки: {response.text}")
    except Exception as e:
        print(f"Не удалось связаться с сервером Kaspi: {str(e)}")


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
    
    # ИСПРАВЛЕНО: Удален атрибут 'xsi:schemaLocation', вызывавший ошибку валидации в Kaspi
    kaspi_catalog = ET.Element('kaspi_catalog', {
        'date': current_date,
        'xmlns': 'kaspiShopping',
        'xmlns:xsi': 'http://w3.org'
    })
    
    # Обязательные поля шапки прайса
    company = ET.SubElement(kaspi_catalog, 'company')
    company.text = "Tabl-kaspi"
    
    merchant_id_elem = ET.SubElement(kaspi_catalog, 'merchantid')
    merchant_id_elem.text = MERCHANT_ID
    
    offers = ET.SubElement(kaspi_catalog, 'offers')
    stores = ['PP1', 'PP2', 'PP3', 'PP4', 'PP5']
    
    for index, row in df.iterrows():
        # Безопасное чтение SKU с защитой от пустых строк и строк-описаний параметров
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
                
                # Умное распознавание текстовых статусов и числовых остатков (1, 2, 50 и т.д.)
                status = 'no'
                if val in ['yes', 'да', 'true']:
                    status = 'yes'
                else:
                    try:
                        # Если в ячейке число, и оно больше нуля — передаем 'yes'
                        if float(val) > 0:
                            status = 'yes'
                    except ValueError:
                        pass
                
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

    # Форматирование и запись структуры в XML-файл
    xml_str = ET.tostring(kaspi_catalog, encoding='utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(encoding='utf-8')
    
    file_name = "price.xml"
    with open(file_name, "wb") as f:
        f.write(pretty_xml)
        
    print(f"Файл {file_name} успешно сгенерирован локально!")
    
    # ПРИНУДИТЕЛЬНЫЙ ИМПОРТ: Отправляем готовый файл в API Kaspi, не дожидаясь их часового таймера
    upload_price_to_kaspi(file_name, KASPI_TOKEN)

if __name__ == "__main__":
    main()
