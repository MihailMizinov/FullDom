import requests
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

import database

telegram_token = "6861771405:AAHcGar4YXikXgIfeh0cKU_6-_Rh2BHNVhA"
yandex_cloud_catalog = "b1gmasb9gep76ibr32ga"
yandex_gpt_api_key = "AQVN2kypilSivP_FGODoaobvzAmweoeI4l0LKsks"
yandex_gpt_model = "yandexgpt-lite"

database = database.Database("database.db")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Представь, что ты директор колледжа. Составь расписание по заданным данным (номер аудиторий, их вместимость, названия групп и их размер. Также учитывай другие данные заданные пользователем, включая возможность добавления физического практикума для заданной группы. В виде:\nаудитория 1-25 вместимость, аудитория 2-30 вместимость, аудитория 3-29 вместимость\nгруппа 1А-15 человек, группа IT078 - 23 человек, группа 3B - 28 человек) в одно время у разных групп занятия идут одновременно в разных аудиториях. Для каждой группы пиши все их пары, включая возможные физические практикумы.\nФормат ответа:\nПара 1: аудитория 1, группа И78\nаудитория 2, группа 1А3, группа Б6 \nПара 2: аудитория 3, группа И78\n аудитория 4, группа 1А\nПара 3: аудитория 5 (физ-практикум) группа И78,\n группа IT078 аудитория 6, \n группа 3B аудитория 2"
    )


async def counter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_prompt = database.get_last_prompt(update.effective_chat.id)
    if last_prompt:
        answer = send_gpt_request(last_prompt, "")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет доступных промптов для обработки.")
        
    counter = database.get_counter(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Количество присланных символов: counter",
    )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_len = len(update.message.text)
    database.add_counter(update.effective_chat.id, text_len)
    system_prompt = (
        "Представь, что ты директор колледжа. Составь расписание по заданным данным (номер аудиторий, их вместимость, названия групп и их размер. Также учитывай другие данные заданные пользователем, включая возможность добавления физического практикума для заданной группы. В виде:\nаудитория 1-25 вместимость, аудитория 2-30 вместимость, аудитория 3-29 вместимость\nгруппа 1А-15 человек, группа IT078 - 23 человек, группа 3B - 28 человек) в одно время у разных групп занятия идут одновременно в разных аудиториях. Для каждой группы пиши все их пары, включая возможные физические практикумы.\nФормат ответа:\nПара 1: аудитория 1, группа И78\nаудитория 2, группа 1А3, группа Б6 \nПара 2: аудитория 3, группа И78\n аудитория 4, группа 1А\nПара 3: аудитория 5 (физ-практикум) группа И78,\n группа IT078 аудитория 6, \n группа 3B аудитория 2"
     )
    database.set_last_prompt(update.effective_chat.id, system_prompt)
    answer = send_gpt_request(system_prompt, update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

def send_gpt_request(system_prompt: str, user_prompt: str):
    body = {
        "modelUri": f"gpt://yandex_cloud_catalog/yandex_gpt_model",
        "completionOptions": "stream": False, "temperature": 0.4, "maxTokens": "2000",
        "messages": [
            "role": "system", "text": system_prompt,
            "role": "user", "text": user_prompt,
        ],
    }
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key yandex_gpt_api_key",
        "x-folder-id": yandex_cloud_catalog,
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        return "ERROR"

    response_json = json.loads(response.text)
    answer = response_json["result"]["alternatives"][0]["message"]["text"]
    if len(answer) == 0:
        return "ERROR"
    
    return answer, user_prompt


if __name__ == "__main__":
    start_handler = CommandHandler("start", start)
    counter_handler = CommandHandler("counter", counter)
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), text)

    application = ApplicationBuilder().token(telegram_token).build()
    application.add_handler(start_handler)
    application.add_handler(counter_handler)
    application.add_handler(text_handler)
    application.run_polling()
