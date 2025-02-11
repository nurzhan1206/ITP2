import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
import threading
import time
from datetime import datetime, timedelta

TOKEN = "7577574516:AAH0nhJq6nIZ4-4ulLrA27yiqvvb0F1qXog"
bot = telebot.TeleBot(TOKEN)


user_data = {}
reminders = {}

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
        time.sleep(30)  # Проверяем каждые 30 секунд

@bot.message_handler(commands=['start'])
def start_message(message: Message):
    bot.send_message(
        message.chat.id,
        "👋 *Привет!* Я бот, который поможет тебе с тренировками и челленджами! 🎯\n\n"
        "📝 Напиши /challenge, чтобы получить случайное задание!\n"
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
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "👇 Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Рассчитать ИМТ")
def ask_height(message: Message):
    bot.send_message(message.chat.id, "📏 Введите ваш *рост* (в см):")
    bot.register_next_step_handler(message, ask_weight)

def ask_weight(message: Message):
    try:
        height = float(message.text)
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
def challengs(message: Message):
    bot.send_message(message.chat.id, "🏆 Вот твой случайный челлендж: [здесь будет функция генерации]")


if __name__ == "__main__":
    threading.Thread(target= reminder_checker, daemon=True).start()
    bot.polling(none_stop=True)
