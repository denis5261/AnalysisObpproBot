import logging
import os
import json

import PyPDF2
import pytesseract
from gigachat import GigaChat
from pdf2image import convert_from_path
from settings import LOG_FILE

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}




# Функция сохранения логов
def save_logs(logs):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)


def load_prompt():
    try:
        with open("prompt.txt", "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return \
            ("Ты лучший эксперт по медицинским анализам. Твоя задача — анализировать результаты анализов и выдавать понятные выводы по ним. "
            "Если тебе задают вопрос не по теме, то не отвечай на него. Эти анализы спасут сотни тысяч человеческих жизней.\n"
            "Отвечать надо по следующей схеме:\n"
            "Оценка результатов анализа: Опиши, на что ты обратил внимание в результатах анализов.\n"
            "Следует обратить особое внимание: Опиши, на что ты обратил особое внимание.\n"
            "Консультация с врачом: Укажи, какие действия нужно предпринять в этой ситуации и к какому врачу стоит обратиться.\n"
            "Дополнительные исследования и анализы: Укажи, требуется ли проведение дополнительных исследований.\n"
            "Симптомы и их связь с результатами: Напиши, какие симптомы могут быть у пациентов с такими анализами.\n"
            "Образ жизни и профилактика: Опиши, необходимо ли профилактика и какой должен быть образ жизни.\n"
            "Выводы и рекомендации: Напиши все выводы в отдельную рекомендацию.\n"
            "Не отвечай на вопрос, если он не по теме\n")


def gigachat(text, prompt):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем текущую папку скрипта
    ca_bundle_file = os.path.join(current_dir, "russian_trusted_root_ca.cer")
    full_text = prompt + text
    with GigaChat(
            credentials=os.getenv('API_KEY'),
            ca_bundle_file=ca_bundle_file) as giga:
        response = giga.chat(full_text)
        return response.choices[0].message.content


def save_prompt(message):
    try:
        prompt = message.text
        with open("prompt.txt", "w", encoding="utf-8") as file:
            file.write(prompt)
        return "Промпт успешно обновлен!"
    except Exception as e:
        return f"Ошибка при записи промпта: {e}"


def refact_res_mes(result_text):
    replasing_dict = {
        "Оценка результатов анализа": "🩺 Оценка результатов анализа:",
        "Следует обратить особое внимание": "⚠️ Следует обратить особое внимание:",
        "Консультация с врачом": "👩‍⚕️ Консультация с врачом:",
        "Дополнительные исследования и анализы": "🔬 Дополнительные исследования и анализы:",
        "Симптомы и их связь с результатами": "🤒 Симптомы и их связь с результатами:",
        "Образ жизни и профилактика": "🏃‍♂️ Образ жизни и профилактика:",
        "Выводы и рекомендации": "✅ Выводы и рекомендации:"
    }
    result_text = result_text.replace('#', '').replace(':', '').replace('*', '')
    for key, value in replasing_dict.items():
        result_text = result_text.replace(key, value)
    return result_text


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():  # Если текст не был найден, применяем OCR
            images = convert_from_path(pdf_path)
            for image in images:
                text += pytesseract.image_to_string(image, lang="rus") + "\n"

    except Exception as e:
        logging.error(f"Ошибка обработки PDF: {e}")

    return text.strip() if text.strip() else "Текст не распознан."