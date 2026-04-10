from sqlalchemy import create_engine, text

engine = create_engine("postgresql://vkr_user:vkr_password@localhost:5432/bank_stability")

with engine.begin() as conn:
    print("Удаление старой таблицы")
    conn.execute(text("DROP TABLE IF EXISTS silver_banks_cleaned CASCADE;"))
    
    print("Создание таблицы с корректными полями")
    conn.execute(text("""
        CREATE TABLE silver_banks_cleaned (
            reg_number INT,
            bank_name TEXT,
            assets FLOAT,
            npl_sum FLOAT,
            capital_sum FLOAT,
            report_date DATE
        );
    """))
    print("Готово. Теперь запусти парсер и загрузку")