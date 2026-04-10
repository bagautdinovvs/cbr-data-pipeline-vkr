import os
import re
import pandas as pd
from dbfread import DBF, FieldParser
from sqlalchemy import create_engine, inspect, text

# Парсер для корректного чтения чисел из DBF
class MyFieldParser(FieldParser):
    def parseN(self, field, data):
        data = data.strip().replace(b'\x00', b'').replace(b',', b'.')
        return float(data) if data else 0

def load_all_to_silver():
    engine = create_engine("postgresql://vkr_user:vkr_password@db:5432/bank_stability")
    table_name = 'silver_banks_cleaned'

    # ШАГ 1: Проверка существующих дат
    existing_dates = []
    inspector = inspect(engine)
    if table_name in inspector.get_table_names():
        with engine.connect() as conn:
            res = pd.read_sql(text(f"SELECT DISTINCT report_date FROM {table_name}"), conn)
            if not res.empty:
                existing_dates = pd.to_datetime(res['report_date']).dt.date.tolist()

    # ШАГ 2: Поиск файлов
    raw_dir = 'raw'
    files_to_process = []
    for root, dirs, files in os.walk(raw_dir):
        for f in files:
            if f.lower().endswith('b1.dbf'):
                files_to_process.append(os.path.join(root, f))

    print(f"Найдено файлов для проверки: {len(files_to_process)}")

    # ШАГ 3: Загрузка
    for data_path in sorted(files_to_process):
        name = os.path.basename(data_path)
        
        # Регулярка вытаскивает все цифры до буквы B. 
        # Обработает и 0124 (ММГГ), и 012024 (ММГГГГ)
        date_match = re.match(r'(\d+)', name)
        if not date_match:
            continue
            
        date_str = date_match.group(1)
        
        try:
            month = int(date_str[:2])
            year_val = int(date_str[2:])
            
            # Если год в формате "24", превращаем в 2024
            if year_val < 100:
                year = 2000 + year_val
            else:
                year = year_val
                
            # Отчетная дата = 1-е число следующего месяца
            report_date = (pd.to_datetime(f"{year}-{month}-01") + pd.DateOffset(months=1)).date()
        except Exception:
            print(f"Ошибка даты в файле: {name}")
            continue

        if report_date in existing_dates:
            print(f"--- {report_date} уже в базе. Пропуск.")
            continue

        print(f">>> Загружаю: {report_date} (файл {name})")

        n1_path = os.path.join(os.path.dirname(data_path), name.lower().replace('b1', 'n1'))
        if not os.path.exists(n1_path):
            continue

        try:
            # Названия банков
            names_dbf = DBF(n1_path, encoding='cp866', parserclass=MyFieldParser)
            names_df = pd.DataFrame(iter(names_dbf))[['REGN', 'NAME_B']]
            names_df.columns = ['reg_number', 'bank_name']

            # Данные баланса
            data_dbf = DBF(data_path, encoding='cp866', parserclass=MyFieldParser)
            df = pd.DataFrame(iter(data_dbf))
            
            df['IITG'] = pd.to_numeric(df['IITG'], errors='coerce').fillna(0)
            df['REGN'] = pd.to_numeric(df['REGN'], errors='coerce')

            # Агрегация
            assets = df.groupby('REGN')['IITG'].sum().reset_index().rename(columns={'REGN':'reg_number', 'IITG':'assets'})
            npl = df[df['NUM_SC'].str.startswith('458', na=False)].groupby('REGN')['IITG'].sum().reset_index().rename(columns={'REGN':'reg_number', 'IITG':'npl_sum'})
            cap = df[df['NUM_SC'].str.startswith(('102','105','106','107','108'), na=False)].groupby('REGN')['IITG'].sum().reset_index().rename(columns={'REGN':'reg_number', 'IITG':'capital_sum'})

            final = names_df.merge(assets, on='reg_number')
            final = final.merge(npl, on='reg_number', how='left')
            final = final.merge(cap, on='reg_number', how='left').fillna(0)
            final['report_date'] = report_date

            final.to_sql(table_name, engine, if_exists='append', index=False)
            print(f"Успешно: {len(final)} строк")

        except Exception as e:
            print(f"Ошибка в {name}: {e}")

if __name__ == "__main__":
    load_all_to_silver()