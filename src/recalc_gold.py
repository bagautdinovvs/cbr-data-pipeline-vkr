import pandas as pd
from sqlalchemy import create_engine

def run_analytics():
    engine = create_engine("postgresql://vkr_user:vkr_password@db:5432/bank_stability")
    
    # Читаем данные, которые загрузил mass_loader
    df = pd.read_sql("SELECT * FROM silver_banks_cleaned", engine)
    df['report_date'] = pd.to_datetime(df['report_date'])

    # Считаем объем всего рынка по датам
    # Это нужно, чтобы вычислить долю каждого банка
    market_by_date = df.groupby('report_date')['assets'].sum().reset_index()
    market_by_date.columns = ['report_date', 'total_market_assets']

    # Соединяем общие данные с данными по рынку
    df = pd.merge(df, market_by_date, on='report_date')

    # Считаем наши главные коэффициенты
    # 1. Доля рынка
    df['market_share'] = df['assets'] / df['total_market_assets']
    
    # 2. Просрочка (NPL) - делим сумму просрочки на активы
    df['npl_ratio'] = df['npl_sum'] / (df['assets'] + 1) # +1 чтобы не делить на ноль
    
    # 3. Достаточность капитала
    df['capital_adequacy'] = df['capital_sum'] / (df['assets'] + 1)

    # Оставляем только нужные колонки для витрины
    final_cols = [
        'reg_number', 'bank_name', 'report_date', 
        'npl_ratio', 'capital_adequacy', 'market_share'
    ]
    gold_df = df[final_cols]

    # Записываем в базу (перезаписываем таблицу полностью)
    gold_df.to_sql('gold_stability_mart', engine, if_exists='replace', index=False)
    print("Витрина данных Gold успешно обновлена!")

if __name__ == "__main__":
    run_analytics()