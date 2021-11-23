# -*- coding: utf8 -*-
import os
#
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, \
    InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import BotBlocked
from aiohttp.helpers import NO_EXTENSIONS
#
import config.initial_config as config
from db_requests import requestDB
from message_object import CompactMessage
#
logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TOKEN, parse_mode='markdown')
dp = Dispatcher(bot)
#


@dp.message_handler(commands=['start'])
async def start_bot_handler(message: types.Message):
    """Функция, выполняемая когда пользователь запускает бота."""
    user_id = message.from_user.id
    #
    await user_processing(user_id)  # проверяем новый ли пользователь
    #
    if check_user_is_operator(user_id) == True:
        markup = get_keyboard('Начать')
        await message.reply(text='Вы оператор, нажмите на кнопку "Начать" чтобы начать принимать и обрабатывать вопросы.',
                            reply=False,
                            reply_markup=markup
                            )
    else:
        await message.reply(text='Напишите свой вопрос и техническая поддержка ответит вам в ближайшее время.',
                            reply=False
                            )


@dp.message_handler(content_types=['text', 'document', 'photo'])
async def message_text_handler(message: types.Message):
    """Функция, выполняемая когда пользователь пишет что-либо боту."""
    user_id = message.from_user.id
    #
    if check_user_in_blocklist(user_id) == False:
        await bot.send_message(chat_id=user_id,
                               text='Вы заблокированы.'
                               )
        return None
    #
    compact_message = CompactMessage(message)
    #
    if check_user_in_dialogs(user_id) == True:
        # Если отправитель сообщения находится в диалоге с кем-либо
        await dialogue_processing(compact_message)
    else:
        if check_user_is_operator(user_id) == True:
            await check_operator_command(compact_message, user_id)
        else:
            await add_ticket_to_db(message=compact_message)
            #
            ticket = compact_message.get_message()
            #
            await mailing_ticket_to_free_operators(ticket)


async def check_operator_command(message: CompactMessage, user_id: int):
    """Проверяет команды оператора."""
    db = requestDB(DB_PATH)
    if message.text == 'Начать':
        db.oper_setStatus(user_id, True)
        #
        markup = get_keyboard('Закончить')
        await bot.send_message(chat_id=user_id,
                               text='Вы начали работу, вам будут приходить вопросы по мере их поступления.',
                               reply_markup=markup
                               )
        #
        await mailing_tickets_to_operator(message.sender_id)
    elif message.text == 'Закончить':
        db.oper_setStatus(user_id, False)
        markup = get_keyboard('Начать')
        await bot.send_message(chat_id=user_id,
                               text='Вы закончили обрабокту вопросов.',
                               reply_markup=markup
                               )
    elif 'ban' in message.text:
        user_id = message.text.replace('ban', '')
        if user_id == '':
            return
        operator_id = message.sender_id
        #
        if int(user_id) in users:
            await ban_user(operator_id, user_id)
        else:
            await bot.send_message(chat_id=operator_id,
                                   text='Пользователя с указанным ID не существует.'
                                   )
    elif 'unblock' in message.text:
        user_id = message.text.replace('unblock', '')
        if user_id == '':
            return
        operator_id = message.sender_id
        #
        if int(user_id) in get_banned_users():
            await unblock_user(operator_id, user_id)
        else:
            await bot.send_message(chat_id=operator_id,
                                   text='Пользователя с указанным ID не существует.'
                                   )
    elif 'connect' in message.text:
        user_id = message.text.replace('connect', '')
        if user_id == '':
            return
        operator_id = message.sender_id
        #
        if int(user_id) in users:
            db.oper_setStatus(operator_id, False)
            db.add_dialogue(operator_id, user_id)
            markup = get_keyboard('Закончить диалог')
            await bot.send_message(chat_id=operator_id,
                                   text=f'Вы подключились к диалогу с пользователем {user_id}.',
                                   reply_markup=markup
                                   )
        else:
            await bot.send_message(chat_id=operator_id,
                                   text='Пользователя с указанным ID не существует.'
                                   )
    db.close()


async def dialogue_processing(message: CompactMessage):
    """Функция обработки диалога между оператором и пользователем."""
    sender_id = message.sender_id
    #
    db = requestDB(DB_PATH)
    dialogue_data = db.get_dialogue(sender_id)
    operator_id = dialogue_data[0]
    questioner_id = dialogue_data[1]
    #
    if sender_id == operator_id:  # Sender is operator
        if message.text == 'Закончить диалог':
            db.oper_setStatus(operator_id, True)
            db.delete_dialogue(operator_id)
            await bot.send_message(chat_id=operator_id,
                                   text='Диалог закончен.',
                                   reply_markup=get_keyboard('Закончить')
                                   )
            await mailing_tickets_to_operator(message.sender_id)
            return None
        #
        if message.text != None:
            text = f"*Оператор {message.sender_first_name}:*\n{message.text}"
        else:
            text = f"*Оператор {message.sender_first_name}:*"
        await send_message(chat_id=questioner_id,
                           message=message,
                           text=text
                           )
        #
    elif sender_id == questioner_id:  # Sender is questioner
        if message.text != None:
            text = f"*{message.sender_first_name}:*\n{message.text}"
        else:
            text = f"*{message.sender_first_name}:*"
        await send_message(chat_id=operator_id,
                           message=message,
                           text=text
                           )
    db.close()


async def add_ticket_to_db(message: CompactMessage):
    '''Добавляет тикет в базу данных.'''
    sender_id = message.sender_id
    sender_first_name = message.sender_first_name
    text = message.text
    file_id = message.file_id
    content_type = message.content_type
    #
    db = requestDB(DB_PATH)
    db.add_ticket_to_db(sender_id, sender_first_name,
                        text, file_id, content_type)
    db.close()


async def mailing_ticket_to_free_operators(ticket: dict):
    """Делает рассылку тикета свободным операторам."""
    freeOperators = get_free_operators()
    for operator in freeOperators:
        oper_id = operator[0]
        #
        sender_id = ticket[0]
        sender_first_name = ticket[1]
        text = ticket[2]
        file = ticket[3]
        content_type = ticket[4]
        #
        if text != None:
            text = f"*{sender_first_name} ({sender_id}):*\n{text}"
        else:
            text = f"*{sender_first_name} ({sender_id})*"
        #
        inline_btn_1 = InlineKeyboardButton(text='Ответить',
                                            callback_data='question' +
                                            str(sender_id)
                                            )
        inline_btn_2 = InlineKeyboardButton(text='Заблокировать',
                                            callback_data='ban' +
                                            str(sender_id)
                                            )
        inline_markup = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2)
        #
        await send_ticket(chat_id=oper_id,
                          content_type=content_type,
                          text=text,
                          file=file,
                          reply_markup=inline_markup
                          )


async def mailing_tickets_to_operator(operator_id: int):
    '''Если есть неотвеченные тикеты бот присылает их оператору.'''
    db = requestDB(DB_PATH)
    tickets = db.get_all_tickets()
    db.close()
    #
    if len(tickets) == 0:
        return
    #
    await bot.send_message(operator_id, text='Ждут ответа:')
    for ticket in tickets:
        sender_id = ticket[0]
        sender_first_name = ticket[1]
        text = ticket[2]
        file = ticket[3]
        content_type = ticket[4]
        #
        if text != None:
            text = f"*{sender_first_name} ({sender_id}):*\n{text}"
        else:
            text = f"*{sender_first_name} ({sender_id})*"
        #
        inline_btn_1 = InlineKeyboardButton(text='Ответить',
                                            callback_data='question' +
                                            str(sender_id)
                                            )
        inline_btn_2 = InlineKeyboardButton(text='Заблокировать',
                                            callback_data='ban' +
                                            str(sender_id)
                                            )
        inline_markup = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2)
        #
        await send_ticket(chat_id=operator_id,
                          content_type=content_type,
                          text=text,
                          file=file,
                          reply_markup=inline_markup
                          )


@dp.callback_query_handler(lambda query: 'question' in query.data)
async def process_callback_question_inl_btn(callback_querry: types.CallbackQuery):
    """Функция, выполняемая когда оператор нажимает на inline-кнопку ответа на тикет."""
    operator_id = callback_querry.from_user.id
    user_id = callback_querry.data.replace('question', '')
    #
    db = requestDB(DB_PATH)
    db.oper_setStatus(operator_id, False)
    db.add_dialogue(operator_id, user_id)
    db.delete_ticket(user_id)
    db.close()
    #
    await bot.send_message(chat_id=user_id,
                           text='Оператор принял ваш вопрос.'
                           )
    await bot.send_message(chat_id=operator_id,
                           text='Вы приняли вопрос.',
                           reply_markup=get_keyboard('Закончить диалог')
                           )


@dp.callback_query_handler(lambda query: 'ban' in query.data)
async def process_callback_ban_inl_btn(callback_querry: types.CallbackQuery):
    """Функция, выполняемая когда оператор нажимает на inline-кнопку блокирования пользователя."""
    operator_id = callback_querry.from_user.id
    user_id = callback_querry.data.replace('ban', '')
    await ban_user(operator_id, user_id)


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    """Функция срабатывает при попытке взаимодействия с пользователем, который заблокировал бота."""
    user_id = update.message.from_user.id
    db = requestDB(DB_PATH)
    db.delete_user(user_id)
    if check_user_is_operator(user_id):
        db.delete_operator(user_id)
    elif check_user_in_dialogs(user_id):
        db.delete_dialogue(user_id)
    db.close()
    return True


async def send_ticket(chat_id: int, content_type, text: str = None, file=None, reply_markup=None):
    """Определяет какого типа тикет и отправляет его."""
    #
    if content_type == 'text':
        await bot.send_message(chat_id=chat_id,
                               text=text,
                               reply_markup=reply_markup
                               )
    elif content_type == 'document':
        await bot.send_document(chat_id=chat_id,
                                document=file,
                                caption=text,
                                reply_markup=reply_markup
                                )
    elif content_type == 'photo':
        await bot.send_photo(chat_id=chat_id,
                             photo=file,
                             caption=text,
                             reply_markup=reply_markup
                             )


async def send_message(chat_id: int, message: CompactMessage, text=None, reply_markup=None):
    """Определяет какого типа сообщение и отправляет его."""
    #
    if message.content_type == 'text':
        await bot.send_message(chat_id=chat_id,
                               text=text,
                               reply_markup=reply_markup
                               )
    elif message.content_type == 'document':
        await bot.send_document(chat_id=chat_id,
                                document=message.file_id,
                                caption=text,
                                reply_markup=reply_markup
                                )
    elif message.content_type == 'photo':
        await bot.send_photo(chat_id=chat_id,
                             photo=message.file_id,
                             caption=text,
                             reply_markup=reply_markup
                             )


async def ban_user(operator_id: int, user_id: int):
    """Блокирует пользователя. Добавляет его в специальную таблицу в БД."""
    db = requestDB(DB_PATH)
    db.ban_user(user_id)
    db.close()
    #
    await bot.send_message(chat_id=operator_id,
                           text=f'Вы заблокировали пользователя {user_id}.'
                           )
    await bot.send_message(chat_id=user_id,
                           text=f'Вы были заблокированы.'
                           )


async def unblock_user(operator_id: int, user_id: int):
    """Разблокирует пользователя. Удаляет его из специальной таблицы в БД."""
    db = requestDB(DB_PATH)
    db.unblock_user(user_id)
    db.close()
    #
    await bot.send_message(chat_id=operator_id,
                           text=f'Вы разблокировали пользователя {user_id}.'
                           )
    await bot.send_message(chat_id=user_id,
                           text=f'Вы были разблокированы.'
                           )


def get_keyboard(text: str) -> types.ReplyKeyboardMarkup:
    """Создает однокнопочную клавиатуру и возвращает её."""
    item = KeyboardButton(text)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(item)
    return markup


def get_users():
    """Получает всех пользователей бота и сохраняет их в глобальную переменную."""
    global users
    db = requestDB(DB_PATH)
    temp = db.get_users()
    for user in temp:
        users.append(user[0])
    db.close()


def get_operators() -> list:
    """Получает всех операторов бота и сохраняет их возвращает их."""
    db = requestDB(DB_PATH)
    operators = db.get_operators()
    db.close()
    return operators


def get_free_operators() -> list:
    """Получает всех свободных операторов бота и сохраняет их возвращает их."""
    db = requestDB(DB_PATH)
    free_operators = db.get_free_operators()
    db.close()
    return free_operators


def check_is_new_user(user_id: int) -> bool:
    """Проверяет нет ли пользователя в БД."""
    if len(users) != 0:
        isNewUser = True
        if user_id in users:
            isNewUser = False
        return isNewUser
    else:  # Если пользователь - первый, кто написал боту
        return True


async def user_processing(user_id: int):
    """Обработка пользователя, запустившего бота."""
    if check_is_new_user(user_id) == True:
        db = requestDB(DB_PATH)
        db.add_user(user_id)
        db.close()
        get_users()


def get_banned_users() -> list:
    """Получает всех заблокированных пользователей из БД и возвращает их."""
    db = requestDB(DB_PATH)
    temp = db.get_users_in_blocklist()
    db.close()
    banned_users = []
    for b_user in temp:
        banned_users.append(b_user[0])
    return banned_users


def check_user_in_blocklist(user_id: int) -> bool:
    """Проверяет нет ли пользователя в БД."""
    banned_users = get_banned_users()
    if user_id in banned_users:
        return False
    return True


def check_user_in_dialogs(user_id: int) -> bool:
    """Проверяет числится ли пользователь в каком-либо из открытых диалогов."""
    db = requestDB(DB_PATH)
    dialogs = db.get_dialogs()
    db.close()
    #
    for dialogue in dialogs:
        if user_id in dialogue:
            return True
    return False


def check_user_is_operator(user_id: int) -> bool:
    """Проверяет является ли пользователь оператором."""
    opers = get_operators()
    for oper in opers:
        if user_id in oper:
            return True
    return False


def main():
    """Главная функция. Запуск бота."""
    global DB_PATH, bot, dp, users
    DB_PATH = config.DB_PATH
    users = []
    #
    if not os.path.isfile(DB_PATH):
        from db_requests import createBD_FromDump
        createBD_FromDump()
    #
    get_users()
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()
