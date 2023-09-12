import telebot
import random
from threading import Timer
from neural_model.neural_model import *
from API_token.API_token import *

bot = telebot.TeleBot(API_TOKEN)

BLACKLIST_FILE = 'blacklist/blacklist.txt'
CSV_FILE = 'users/users.csv'

total_stickers_sent = 0
message_delete_users = {}

def read_csv():
    with open(CSV_FILE, 'r') as file:
        return list(csv.reader(file))

def write_csv(data):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def train_model_for_all_users(message):
    data = read_csv()
    model = build_model()
    train_model(model)

    for index, row in enumerate(data):
        user_id = row[0]
        score = evaluate_user(user_id, model)
        if len(row) == 5:
            data[index].append(score)
        else:
            data[index][5] = score

    write_csv(data)
    bot.reply_to(message, "Обучение завершено и результаты обновлены.")

def reset_total_stickers():
    global total_stickers_sent
    total_stickers_sent = 0


def stop_message_deletion(user_id):
    message_delete_users.pop(user_id, None)

def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as file:
            return set(line.strip() for line in file.readlines())
    except FileNotFoundError:
        return set()

def save_to_blacklist(user_id):
    with open(BLACKLIST_FILE, 'a') as file:
        file.write(f"{user_id}\n")
blacklist = load_blacklist()

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, "Я каменьщик, работаю три дня")

@bot.message_handler(commands=['stats'])
def send_message(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)

    if user_data:
        score = float(user_data[5])

        bot.reply_to(message, "Ваш социальный рейтинг: " + str(round(50 * (score + 1))) + " кредитов")
    else:
        bot.reply_to(message, "Ваш социальный рейтинг: 50 кредитов")


@bot.message_handler(commands=['train'])
def handle_train_command(message):
    train_model_for_all_users(message)


@bot.message_handler(commands=['blackList'])
def add_to_blacklist(message):
    if message.reply_to_message:
        user_id = str(message.reply_to_message.from_user.id)
        if user_id not in blacklist:
            blacklist.add(user_id)
            save_to_blacklist(user_id)
            bot.reply_to(message,
                         f"Пользователь {message.reply_to_message.from_user.first_name} добавлен в черный список!")


@bot.message_handler(commands=['RussianRoulette'])
def russian_roulette(message):
    user_id = message.from_user.id
    if random.randint(1, 6) == 1:
        message_delete_users[user_id] = True
        bot.reply_to(message, "Вы проиграли! Ваши сообщения будут удаляться в течение следующих 30 минут.")
        Timer(1800, stop_message_deletion, args=[user_id]).start()
    else:
        bot.reply_to(message, "Поздравляем! Вы выиграли в русскую рулетку.")


def init_csv():
    try:
        with open(CSV_FILE, 'x') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'messages', 'stickers', 'ban_word', 'warns'])
    except FileExistsError:
        pass


def add_user_to_csv(user_id):
    with open(CSV_FILE, 'a') as file:
        writer = csv.writer(file)
        writer.writerow([user_id, 0, 0, 0, 0])


def get_user_data(user_id):
    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                return row
    return None


def update_user_data(user_id, messages=0, stickers=0, ban_word=0, warns=0):
    data = []
    user_data = get_user_data(user_id)

    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                data.append([user_id,
                             int(user_data[1]) + messages,
                             int(user_data[2]) + stickers,
                             int(user_data[3]) + ban_word,
                             int(user_data[4]) + warns])
            else:
                data.append(row)

    with open(CSV_FILE, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(data)

@bot.message_handler(func=lambda message: message.reply_to_message is not None)
def handle_replies(message):
    text = message.text.lower()
    user_id = str(message.reply_to_message.from_user.id)

    if "спасибо" in text:
        user_data = get_user_data(user_id)
        if user_data:
            update_user_data(user_id, warns=1)


@bot.message_handler(func=lambda m: True)  # Обработчик для всех сообщений
def handle_all_messages(message):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id)

    if not user_data:
        add_user_to_csv(user_id)

    update_user_data(user_id, messages=1)


@bot.message_handler(func=lambda message: message.from_user.id in message_delete_users)
def delete_users_message(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    user_id = str(message.from_user.id)
    update_user_data(user_id, ban_word=1)



@bot.message_handler(content_types=['sticker'])
def delete_sticker(message):
    global total_stickers_sent
    user_id = str(message.from_user.id)

    if user_id in blacklist:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return

    total_stickers_sent += 1
    update_user_data(user_id, stickers=1)

    if total_stickers_sent == 1:
        Timer(60, reset_total_stickers).start()

    if total_stickers_sent > 5:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)



init_csv()
bot.infinity_polling()
