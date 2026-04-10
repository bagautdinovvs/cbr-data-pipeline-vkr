import os
import requests
import zipfile
from datetime import datetime
from dateutil.relativedelta import relativedelta

def download_data():
    # Настройки путей
    raw_path = 'raw'
    if not os.path.exists(raw_path):
        os.makedirs(raw_path)

    # Проверяем последние два месяца, т.к. ЦБ выкладывает данные не сразу
    today = datetime.now()
    
    for i in [1, 2]:
        target_date = today - relativedelta(months=i)
        period = target_date.strftime("%Y%m")
        file_name = f"101-{period}01.zip"
        
        # Ссылка на архив ЦБ
        url = f"https://www.cbr.ru/vfs/finmarkets/files/exp/{file_name}"
        folder_to_save = os.path.join(raw_path, period)

        # Если папка уже есть, значит мы это уже скачивали
        if os.path.exists(folder_to_save):
            print(f"Период {period} уже есть, пропускаю.")
            continue

        print(f"Пробую скачать данные за {period}...")
        res = requests.get(url)
        
        if res.status_code == 200:
            # Сохраняем временный архив
            temp_zip = "temp.zip"
            with open(temp_zip, "wb") as f:
                f.write(res.content)
            
            # Распаковываем
            with zipfile.ZipFile(temp_zip, 'r') as z:
                z.extractall(folder_to_save)
            
            os.remove(temp_zip)
            print(f"Готово! Данные за {period} скачаны.")
            break # Скачали самое свежее — и хватит
        else:
            print(f"Файла за {period} еще нет на сайте ЦБ.")

if __name__ == "__main__":
    download_data()