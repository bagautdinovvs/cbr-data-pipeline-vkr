import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from forecast import get_forecast_for_bank # Подключаем твой ML-прогноз

st.set_page_config(page_title="Мониторинг банков", layout="wide")

# Подключаемся к нашей базе
db_url = "postgresql://vkr_user:vkr_password@db:5432/bank_stability"
engine = create_engine(db_url)

def get_data():
    # Тянем из Gold
    return pd.read_sql("SELECT * FROM gold_stability_mart ORDER BY report_date", engine)

st.title("Анализ финансовой устойчивости банков")
st.write("Данные получены из отчетности ЦБ РФ (форма 101)")

df = get_data()

if not df.empty:
    # Выбор банка в боковой панели
    banks = df['bank_name'].unique()
    selected_bank = st.sidebar.selectbox("Выберите банк из списка:", sorted(banks))
    
    # Фильтруем данные только по этому банку
    bank_data = df[df['bank_name'] == selected_bank].copy()
    bank_data['report_date'] = pd.to_datetime(bank_data['report_date'])
    
    # Последние цифры для плашек сверху
    last = bank_data.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Уровень просрочки", f"{last['npl_ratio']:.2%}")
    col2.metric("Запас капитала", f"{last['capital_adequacy']:.2%}")
    col3.metric("Доля рынка", f"{last['market_share']:.4%}")

    st.markdown("---")

    # Главный график: Просрочка + ML Прогноз
    st.subheader("Динамика кредитного риска (NPL) и прогноз")
    
    # Запускаем скрипт прогнозирования
    reg_num = last['reg_number']
    forecast_df = get_forecast_for_bank(reg_num)

    fig_npl = go.Figure()
    # Реальные данные
    fig_npl.add_trace(go.Scatter(x=bank_data['report_date'], y=bank_data['npl_ratio'], 
                                 name="Факт", line=dict(color='blue', width=3)))
    
    # Если прогноз посчитался — рисуем его
    if isinstance(forecast_df, pd.DataFrame):
        fig_npl.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_npl'], 
                                     name="Прогноз ML", line=dict(color='red', dash='dash')))

    st.plotly_chart(fig_npl, use_container_width=True)

    # Нижний ряд: Капитал и Доля рынка
    left, right = st.columns(2)
    
    with left:
        st.subheader("Устойчивость капитала")
        f_cap = go.Figure(go.Scatter(x=bank_data['report_date'], y=bank_data['capital_adequacy'], 
                                     fill='tozeroy', line=dict(color='green')))
        st.plotly_chart(f_cap, use_container_width=True)
        
    with right:
        st.subheader("Изменение доли рынка")
        f_share = go.Figure(go.Scatter(x=bank_data['report_date'], y=bank_data['market_share'], 
                                       mode='lines+markers', line=dict(color='orange')))
        st.plotly_chart(f_share, use_container_width=True)

    # Детальная таблица
    if st.checkbox("Показать таблицу с данными"):
        st.write(bank_data.sort_values('report_date', ascending=False))

else:
    st.error("БД пуста. Запусти парсер и загрузку")