# run_pipeline.py
import subprocess
import sys

scripts = [
    "src/cbr_downloader.py",
    "src/cbr_mass_loader.py",
    "src/recalc_gold.py",
    "src/forecast.py"
]

def run():
    print("Запуск еженедельного обновления данных")
    for script in scripts:
        print(f"Запуск {script}...")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"Ошибка при выполнении {script}. Остановка пайплайна.")
            return
    print("Обновление завершено успешно!")

if __name__ == "__main__":
    run()