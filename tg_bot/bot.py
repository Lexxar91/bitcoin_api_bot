import os

import telebot
from dotenv import load_dotenv

import client

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')
admin = os.getenv('TG_ADMIN_ID')

bot = telebot.TeleBot(bot_token)

states_list = ["ADDRESS", "AMOUNT", "CONFIRM"]
states_of_users = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    """
    markup: создаем объект для работы с кнопками (row_width - определяет количество кнопок по ширине)
    создаем три кнопки, типа:KeyboardButton
    отправляем пользователю три кнопки типа:KeyboardButton
    после команды /start.
    """

    try:
        client.create_user({"tg_ID": message.from_user.id,
                           "nick": message.from_user.username})

    except Exception as e:
        return e

    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=3,
        resize_keyboard=True
    )

    btn1 = telebot.types.KeyboardButton('Кошелек')
    btn2 = telebot.types.KeyboardButton('Перевести')
    btn3 = telebot.types.KeyboardButton('История')
    btn4 = telebot.types.KeyboardButton('Админ')

    markup.add(btn1, btn2, btn3, btn4)

    text: str = f'Привет {message.from_user.full_name}, я твой бот-криптокошелек, \n' \
                'у меня ты можешь хранить и отправлять биткоины'

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Кошелек')
def wallet(message):
    wallet = client.get_user_wallet_by_tg_id(message.from_user.id)
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)

    text = (f'Ваш баланс: {wallet["balance"]} BTC \n'
            f'Ваш адрес: {wallet["address"]}')
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='История транзакций')
def history(message):
    transactions = client.get_user_transactions(
        client.get_user_by_tg_id(message.from_user.id)["id"])

    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)

    text = f'Ваши транзакции: \n{transactions}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Перевести')
def transaction(message):
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Введите адрес кошелька куда хотите перевести: '
    bot.send_message(message.chat.id, text, reply_markup=markup)
    # тут мы даём юзеру состояние при котором ему будет возвращаться следующее
    # сообщение
    states_of_users[message.from_user.id] = {"STATE": "ADDRESS"}


@bot.message_handler(regexp='История')
def history(message):
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    transactions = ['1', '2', '3']  # сюда мы загрузим транзакции
    text = f'Ваши транзакции{transactions}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Меню')
def menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btn1 = telebot.types.KeyboardButton('Кошелек')
    btn2 = telebot.types.KeyboardButton('Перевести')
    btn3 = telebot.types.KeyboardButton('История')

    markup.add(btn1, btn2, btn3)

    text = f'Главное меню'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id ==
                     admin and message.text == 'Админ')
def admin_panel(message):
    if message.from_user.id != admin:
        markup = telebot.types.ReplyKeyboardMarkup(
            row_width=2,
            resize_keyboard=True
        )
        btn1 = telebot.types.KeyboardButton('Меню')
        markup.add(btn1)
        bot.send_message(
            message.chat.id,
            'У вас нет прав администратора.',
            reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(
            row_width=2, resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton('Общий баланс')
        btn2 = telebot.types.KeyboardButton('Все юзеры')
        btn3 = telebot.types.KeyboardButton('Данные по юзеру')
        btn4 = telebot.types.KeyboardButton('Удалить юзера')
        markup.add(btn1, btn2, btn3, btn4)

        text = f'Админ-панель'
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id ==
                     admin and message.text == "Все юзеры")
def show_all_users(message):
    text = f'Юзеры:'
    users = client.get_users()

    inline_markup = telebot.types.InlineKeyboardMarkup()
    for user in users:
        inline_markup.add(telebot.types.InlineKeyboardButton(
            text=f'Юзер: {user["tg_ID"]}',
            callback_data=f'user_{user["tg_ID"]}'
        ))
    bot.send_message(message.chat.id, text, reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    query_type = call.data.split('_')[0]
    users = client.get_users()

    if query_type == 'user':
        user_id = call.data.split('_')[1]
        inline_markup = telebot.types.InlineKeyboardMarkup()
        for user in users:
            if str(user['tg_ID']) == user_id:
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(
                        text="Назад",
                        callback_data='users'),
                    telebot.types.InlineKeyboardButton(
                        text="Удалить юзера",
                        callback_data=f'delete_user_{user_id}'))

                bot.edit_message_text(
                    text=f'Данные по юзеру:\n'
                    f'ID: {user["tg_ID"]}\n'
                    f'Ник: {user.get("nick")}\n'
                    f'Баланс: {client.get_user_balance_by_id(user["id"])}',
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=inline_markup)
                print(f"Запрошен {user}")
                break

    if query_type == 'users':
        inline_markup = telebot.types.InlineKeyboardMarkup()
        for user in users:
            inline_markup.add(
                telebot.types.InlineKeyboardButton(
                    text=f'Юзер: {user["tg_ID"]}',
                    callback_data=f"user_{user['tg_ID']}"))
        bot.edit_message_text(
            text="Юзеры:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=inline_markup)  # прикрепляем нашу разметку к ответному сообщению

    if query_type == 'delete' and call.data.split('_')[1] == 'user':

        user_id = int(call.data.split('_')[2])
        for i, user in enumerate(users):
            if user['tg_ID'] == user_id:
                print(f'Удален Юзер: {users[i]}')
                client.delete_user(users.pop(i)['id'])
        inline_markup = telebot.types.InlineKeyboardMarkup()
        for user in users:
            inline_markup.add(
                telebot.types.InlineKeyboardButton(
                    text=f'Юзер: {user["tg_ID"]}',
                    callback_data=f"user_{user['tg_ID']}"))
        bot.edit_message_text(
            text="Юзеры:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=inline_markup
        )


@bot.message_handler(func=lambda message: message.from_user.id ==
                     admin and message.text == "Общий баланс")
def total_balance(message):
    total_bal = client.get_total_balance()
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btn1 = telebot.types.KeyboardButton('Меню')
    btn2 = telebot.types.KeyboardButton('Админка')
    markup.add(btn1, btn2)

    text = f'Общий баланс: {total_bal} BTC'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(
    func=lambda message: states_of_users.get(
        message.from_user.id)["STATE"] == 'AMOUNT')
def get_confirmation_of_transaction(message):
    if message.text == "Меню":
        del states_of_users[message.from_user.id]
        menu(message)
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    if message.text.isdigit():
        text = f'Вы хотите перевести {message.text} сатоши,\n' \
               f'на биткоин-адрес {states_of_users[message.from_user.id]["ADDRESS"]}: '
        confirm = telebot.types.KeyboardButton('Подтверждаю')
        markup.add(confirm)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        # тут мы даём юзеру состояние при котором ему будет возвращаться
        # следующее сообщение
        states_of_users[message.from_user.id]["STATE"] = "CONFIRM"
        states_of_users[message.from_user.id]["AMOUNT"] = int(message.text)
    else:
        text = f'Вы ввели не число, попробуйте заново: '
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(
    func=lambda message: states_of_users.get(
        message.from_user.id)["STATE"] == 'CONFIRM')
def get_hash_of_transaction(message):
    if message.text == "Меню":
        del states_of_users[message.from_user.id]
        menu(message)
    elif message.text == "Подтверждаю":
        bot.send_message(
            message.chat.id,
            f" Ваша транзакция: " + str(client.create_transaction(message.from_user.id,
                                                                  states_of_users[message.from_user.id]['ADDRESS'],
                                                                  states_of_users[message.from_user.id]['AMOUNT']))
        )
        del states_of_users[message.from_user.id]
        menu(message)


@bot.message_handler(
    func=lambda message: states_of_users.get(
        message.from_user.id)["STATE"] == 'ADDRESS')
def get_amount_of_transaction(message):
    if message.text == "Меню":
        del states_of_users[message.from_user.id]
        menu(message)
    markup = telebot.types.ReplyKeyboardMarkup(
        row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Введите сумму в сатоши, которую хотите перевести: '
    bot.send_message(message.chat.id, text, reply_markup=markup)
    # тут мы даём юзеру состояние при котором ему будет возвращаться следующее
    # сообщение
    states_of_users[message.from_user.id]["STATE"] = "AMOUNT"
    states_of_users[message.from_user.id]["ADDRESS"] = message.text


bot.infinity_polling(timeout=10)
