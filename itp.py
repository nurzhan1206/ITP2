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
                    bot.send_message(user_id, f"Напоминание: {message}")
                    reminders[user_id].remove(reminder)
            if not reminders[user_id]:
                del reminders[user_id]
        time.sleep(30)  # Проверяем раз в 30 секунд

@bot.message_handler(commands=['start'])
def start_message(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("Рассчитать ИМТ")
    btn2 = KeyboardButton("Установить напоминание")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Выберите, что вы хотите сделать:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Рассчитать ИМТ")
def ask_name(message: Message):
    bot.send_message(message.chat.id, "Как вас зовут?")
    bot.register_next_step_handler(message, ask_height)

def ask_height(message: Message):
    user_data[message.chat.id] = {"name": message.text}
    bot.send_message(message.chat.id, "Какой у вас рост? (в см)")
    bot.register_next_step_handler(message, ask_weight)

def ask_weight(message: Message):
    try:
        height = float(message.text)
        user_data[message.chat.id]["height"] = height
        bot.send_message(message.chat.id, "Какой у вас вес? (в кг)")
        bot.register_next_step_handler(message, calculate_bmi)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное число для роста.")
        bot.register_next_step_handler(message, ask_weight)

def calculate_bmi(message: Message):
    try:
        weight = float(message.text)
        height = user_data[message.chat.id]["height"] / 100
        bmi = weight / (height ** 2)
        bot.send_message(message.chat.id, f"Ваш ИМТ: {bmi:.2f}. Здоровый диапазон: 18.5 - 24.9.")
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное число для веса.")
        bot.register_next_step_handler(message, calculate_bmi)

@bot.message_handler(func=lambda message: message.text == "Установить напоминание")
def set_reminder_prompt(message: Message):
    bot.send_message(message.chat.id, "Введите напоминание в формате: HH:MM Текст напоминания")
    bot.register_next_step_handler(message, set_reminder)

def set_reminder(message: Message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Использование: HH:MM Тренировка в зале")
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

        bot.send_message(user_id, f"Напоминание установлено на {time_str}: {reminder_text}")
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный формат. Используйте HH:MM Текст.")

if __name__ == "__main__":
    threading.Thread(target=reminder_checker, daemon=True).start()
    bot.polling(none_stop=True)
