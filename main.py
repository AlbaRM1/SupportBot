import os
import logging

from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.environ.get('API_TOKEN')

# Config Logging
logging.basicConfig(level=logging.INFO)

# Initialization bot
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_message(message: types.Message):
    await message.answer('Привет! Это бот для связи с саппортом нашего проекта.\nПросим вас не флудить/спамить и тогда наши саппорты смогут вам помочь!\nМожешь написать вопрос, на него обязательно ответят!')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)