from yandex_cloud_ml_sdk import YCloudML
import os
from dotenv import load_dotenv
import sys
import re

# Функция для очистки текста от суррогатных пар
def clean_text(text):
    """Очищает текст от суррогатных пар и некорректных символов."""
    return re.sub(r'[\ud800-\udfff]', '', text)

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем API-ключ и folder_id из переменных окружения
API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

if not API_KEY or not FOLDER_ID:
    print("Ошибка: YANDEX_API_KEY или YANDEX_FOLDER_ID не найдены. Убедитесь, что они указаны в .env файле.")
    sys.exit(1)

# Инициализация SDK
sdk = YCloudML(folder_id=FOLDER_ID, auth=API_KEY)

# Настройка модели
model = sdk.models.completions("yandexgpt-lite", model_version="latest")
model = model.configure(temperature=0.3)

# Хранилище истории чата
chat_history = []

def ask_yandex_gpt(prompt):
    """Отправляет запрос к YandexGPT с учётом истории чата и возвращает текст ответа."""
    # Очищаем текст запроса
    cleaned_prompt = clean_text(prompt)
    
    # Добавляем новый запрос пользователя в историю
    chat_history.append({"role": "user", "text": cleaned_prompt})
    
    try:
        # Отправляем полную историю чата
        result = model.run(chat_history)
        # Извлекаем текст ответа
        for alternative in result:
            response_text = clean_text(alternative.text)
            # Добавляем ответ модели в историю
            chat_history.append({"role": "assistant", "text": response_text})
            return response_text
    except UnicodeEncodeError as e:
        return f"Ошибка кодировки: {e}. Попробуйте убрать специальные символы из запроса."
    except Exception as e:
        return f"Ошибка при запросе к API: {e}"

def main():
    print("Чат с YandexGPT. Введите 'exit' для завершения.")
    
    while True:
        try:
            # Запрашиваем ввод пользователя
            prompt = input(">>> ").strip()
            
            # Проверяем команду выхода
            if prompt.lower() == "exit":
                print("Завершение работы.")
                break
            
            # Проверяем, пустой ли запрос
            if not prompt:
                print("Ошибка: Запрос не может быть пустым.")
                continue
            
            # Отправляем запрос и выводим ответ
            response = ask_yandex_gpt(prompt)
            print(response)
            
        except KeyboardInterrupt:
            print("\nЗавершение работы по прерыванию.")
            break
        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
