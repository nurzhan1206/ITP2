import random
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
import threading
import time
from datetime import datetime, timedelta
import json
import os

with open("kick.json", "r") as json_file:
    a = json.load(json_file)


TELEGRAM_TOKEN = a["telegram_token"]
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_challenges = {}
user_data = {}
reminders = {}
CHALLENGES_FILE = "challenges.json"
DATA_FILE = "challenges.json"

def load_challenges():
    if os.path.exists(CHALLENGES_FILE):
        with open(CHALLENGES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def save_challenges(challenges):
    with open(CHALLENGES_FILE, "w", encoding="utf-8") as file:
        json.dump(challenges, file, indent=4, ensure_ascii=False)


challenges = [
    "Сделать 100 отжиманий",
    "Сделать 100 приседаний",
    "Сделать 50 подтягиваний",
    "Пробежать 5 км",
    "Встать в планку на 5 минут",
    "Отказаться от сладкого на 3 дня",
    "Сделать 200 прыжков на скакалке",
    "Пройти 10 000 шагов за день"
]

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

def reminder_checker():
    while True:
        now = datetime.now()
        for user_id, user_reminders in list(reminders.items()):
            for reminder in user_reminders:
                reminder_time, message = reminder
                if now >= reminder_time:
                    bot.send_message(user_id, f"⏰ Напоминание: *{message}*")
                    reminders[user_id].remove(reminder)
            if not reminders[user_id]:
                del reminders[user_id]
        time.sleep(30)

@bot.message_handler(commands=['start'])
def start_message(message: Message):
    bot.send_message(
        message.chat.id,
        "👋 *Привет!* Я бот, который поможет тебе с тренировками и челленджами! 🎯\n\n"
        "📝 Помоги нам стать лучше, напиши отзыв сюда /reviews !\n"
        "📌 Также я могу напоминать тебе о тренировках. Напиши 'Установить напоминание'!"
    )
    bot.send_message(message.chat.id, "Как вас зовут?")
    user_data[message.chat.id] = {"name": message.text}
    bot.register_next_step_handler(message, func)

def func(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("📊 Рассчитать ИМТ")
    btn2 = KeyboardButton("⏰ Установить напоминание")
    btn3 = KeyboardButton("📸 Фото еды")
    btn4 = KeyboardButton("🔥 Челлендж дня")
    btn5 = KeyboardButton("🔥 Твои челленджы")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id, "👇 Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Рассчитать ИМТ")
def ask_height(message: Message):
    bot.send_message(message.chat.id, "📏 Введите ваш *рост* (в см):")
    bot.register_next_step_handler(message, ask_weight)

def ask_weight(message: Message):
    try:
        height = float(message.text)

        # Проверка, есть ли user_id в user_data
        if message.chat.id not in user_data:
            user_data[message.chat.id] = {}

        user_data[message.chat.id]["height"] = height
        bot.send_message(message.chat.id, "⚖️ Теперь введите ваш *вес* (в кг):")
        bot.register_next_step_handler(message, calculate_bmi)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите *число* для роста (например: 175).")
        bot.register_next_step_handler(message, ask_weight)

def calculate_bmi(message: Message):
    try:
        weight = float(message.text)
        height = user_data[message.chat.id]["height"] / 100
        bmi = weight / (height ** 2)
        bot.send_message(
            message.chat.id,
            f"🧮 Ваш *ИМТ*: `{bmi:.2f}`\n\n"
            "🔹 _Норма_: 18.5 - 24.9\n"
            "🔹 _Избыточный вес_: 25 - 29.9\n"
            "🔹 _Ожирение_: 30+"
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректное *число* для веса.")
        bot.register_next_step_handler(message, calculate_bmi)

@bot.message_handler(func=lambda message: message.text == "⏰ Установить напоминание")
def set_reminder_prompt(message: Message):
    bot.send_message(
        message.chat.id,
        "⏳ Введите напоминание в формате: `HH:MM Текст напоминания`\n\n"
        "📌 *Пример:* `07:30 Утренняя тренировка`"
    )
    bot.register_next_step_handler(message, set_reminder)

def set_reminder(message: Message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ *Ошибка!* Используйте формат: `HH:MM Тренировка в зале`")
            return

        time_str, reminder_text = parts[0], parts[1]
        reminder_time = datetime.strptime(time_str, "%H:%M").time()
        now = datetime.now()
        reminder_datetime = datetime.combine(now.date(), reminder_time)

        if reminder_datetime < now:
            reminder_datetime += timedelta(days=1)

        user_id = message.chat.id
        if user_id not in reminders:
            reminders[user_id] = []
        reminders[user_id].append((reminder_datetime, reminder_text))

        bot.send_message(user_id, f"✅ Напоминание установлено на *{time_str}*: _{reminder_text}_")
    except ValueError:
        bot.send_message(message.chat.id, "❌ *Ошибка!* Используйте формат: `HH:MM Текст`.")

@bot.message_handler(func=lambda message: message.text == "📸 Фото еды")
def photo_kcal(message: Message):
    bot.send_message(message.chat.id, "📷 Сфотографируйте ваш прием пищи!")

@bot.message_handler(func=lambda message: message.text == "🔥 Челлендж дня")
@bot.message_handler(func=lambda message: message.text == "🔥 Челлендж дня")
def give_challenge(message):
    user_id = str(message.chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in user_data:
        user_data[user_id] = {"active": [], "completed": [], "last_challenge_date": "", "challenge_count": 0}

    if user_data[user_id]["last_challenge_date"] == today and user_data[user_id]["challenge_count"] >= 3:
        bot.send_message(user_id, "⚠ Ты уже взял 3 челленджа на сегодня! Попробуй завтра 💪")
        return

    available_challenges = [ch for ch in challenges if ch not in user_data[user_id]["active"]]

    challenge = random.choice(available_challenges)
    user_data[user_id]["active"].append(challenge)
    user_data[user_id]["last_challenge_date"] = today
    user_data[user_id]["challenge_count"] += 1

    save_data()

    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{challenge}")
    markup.add(button)

    bot.send_message(user_id, f"🔥 Твой челлендж: {challenge}\n\n"
                              "Когда ты его выполнишь, нажми на кнопку ниже 👇", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def complete_challenge(call):
    user_id = str(call.message.chat.id)
    challenge = call.data[5:]

    if user_id in user_data and challenge in user_data[user_id]["active"]:
        user_data[user_id]["active"].remove(challenge)
        user_data[user_id]["completed"].append(challenge)
        save_data()

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=f"✅ Челлендж выполнен: {challenge} 💪")

@bot.message_handler(func=lambda message: message.text == "🔥 Твои челленджы")
def list_challenges(message):
    user_id = str(message.chat.id)
    active = user_data.get(user_id, {}).get("active", [])
    completed = user_data.get(user_id, {}).get("completed", [])

    response = "📋 *Твои челленджи:*\n\n"

    if active:
        response += "🔥 *Активные челленджи:*\n" + "\n".join([f"▪ {ch}" for ch in active]) + "\n\n"
    else:
        response += "🔥 *Активные челленджи:* Нет активных челленджей.\n\n"

    if completed:
        response += "✅ *Выполненные челленджи:*\n" + "\n".join([f"✔ {ch}" for ch in completed])
    else:
        response += "✅ *Выполненные челленджи:* Пока нет выполненных челленджей."

    bot.send_message(user_id, response, parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target= reminder_checker, daemon=True).start()
    bot.polling(none_stop=True)
