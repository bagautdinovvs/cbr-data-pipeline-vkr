import pandas as pd
import numpy as np
from sqlalchemy import create_engine

def get_forecast_for_bank(reg_number):
    """
    Функция берет историю NPL банка и предсказывает значения на 3 месяца вперед.
    Используем метод простого экспоненциального сглаживания.
    """
    engine = create_engine("postgresql://vkr_user:vkr_password@db:5432/bank_stability")
    
    # 1. Загружаем историю просрочки для конкретного банка
    query = f"""
        SELECT report_date, npl_ratio 
        FROM gold_stability_mart 
        WHERE reg_number = {reg_number} 
        ORDER BY report_date
    """
    df = pd.read_sql(query, engine)
    
    # Если данных мало (меньше 6 месяцев), прогноз строить бессмысленно
    if len(df) < 6:
        return None

    # Подготавливаем данные
    df['report_date'] = pd.to_datetime(df['report_date'])
    history = df['npl_ratio'].values
    last_date = df['report_date'].max()

    # 2. Прогноз
    # Мы берем последние значения с разным весом (свежие данные важнее старых)
    # alpha — это коэффициент "доверия" к последним изменениям
    alpha = 0.3
    forecast_value = history[-1] # Начинаем с последней точки
    
    # Считаем сглаженное среднее (простейшая модель)
    for i in range(len(history)):
        forecast_value = alpha * history[i] + (1 - alpha) * forecast_value

    # 3. Генерим будущие даты
    # Создаем 3 следующие точки (месяца)
    future_dates = []
    future_values = []
    
    current_f_date = last_date
    for _ in range(3):
        current_f_date = current_f_date + pd.DateOffset(months=1)
        future_dates.append(current_f_date)
        
        # Добавляем немного "тренда" (разница между последними двумя месяцами)
        trend = history[-1] - history[-2]
        # Предсказанное значение = наше сглаженное + затухающий тренд
        prediction = forecast_value + (trend * 0.5)
        
        # Чтобы прогноз не уходил в минус (риск не может быть отрицательным)
        if prediction < 0: prediction = 0
        
        future_values.append(prediction)
        # Обновляем базу для следующего шага
        forecast_value = prediction 

    # Собираем результат в красивую табличку
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'forecast_npl': future_values
    })
    
    return forecast_df

if __name__ == "__main__":
    # Тестовый запуск для проверки (рандомный банк)
    test_reg = 1481 
    res = get_forecast_for_bank(test_reg)
    if res is not None:
        print("Прогноз на ближайшие 3 месяца:")
        print(res)