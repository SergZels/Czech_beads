from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import os.path
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.dispatcher.handler import CancelHandler
import conf
# from aiogram.dispatcher.middlewares import BaseMiddleware
from loguru import logger
from aiogram.utils.executor import start_webhook


TEST_MODE = False

if conf.VPS:
    TEST_MODE = False

##------------------Блок ініціалізації-----------------##
if TEST_MODE:
    API_Token = conf.API_TOKEN_Test
else:
    API_Token = conf.TOKEN

ADMIN_ID = conf.ADMIN_ID

bot = Bot(token=API_Token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logger.add("debug.txt")
# webhook settings
WEBHOOK_HOST = 'https://vmi957205.contaboserver.net'
WEBHOOK_PATH = '/prod_chbeads'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '0.0.0.0'  # or ip 127.0.0.1
WEBAPP_PORT = 3010

# ##---------------------Midelware-------------------------------##
#
#
# class MidlWare(BaseMiddleware):
#
#     async def on_process_update(self, update: types.Update, date: dict):
#         logger.debug(update)
#         logger.debug(update.message.from_user.id)
#         if update.message.from_user.id not in ADMIN_ID:
#             logger.debug(f"Хтось лівий зайшов {update.message.from_user.id}")
#             raise CancelHandler()

##-------------------handlers--------------------------------------##
@dp.message_handler(commands=['start', 'help'], state= None)
async def send_welcome(message: types.Message):
    await message.reply("Вітаю! Введи код бісеру!")

##----------------------------Різне----------------------##
@dp.message_handler()
async def echo(message : types.Message):
    logger.debug(f'User {message.from_user.id} type {message.text}')
    if message.text == "Файл12":
        doc = open('debug.txt', 'rb')
        await message.reply_document(doc)
    elif message.text.isdigit():
        if len(message.text) == 5:
            check_file = os.path.exists(f'biser_pic/c{message.text}.jpg')
            if check_file:
                doc = open(f'biser_pic\c{message.text}.jpg', 'rb')
                await message.reply_photo(doc)
            else:
                await message.answer("Нажаль такого бісеру немає в моїй базі даних!")

        else:
            await message.answer("Коди чеського бісеру 5 ти значні!")
    else:
        await message.answer("Будь - ласка введіть код бісеру")
    
##-------------------Запуск бота-------------------------##
if TEST_MODE:
    print("Bot running...")
    # dp.middleware.setup(MidlWare())
    executor.start_polling(dp, skip_updates=True)
else:
    async def on_startup(dp):
        await bot.set_webhook(WEBHOOK_URL)
        logger.debug("Бот запущено!")

    async def on_shutdown(dp):
        logger.debug('Зупиняюся!')
        await bot.delete_webhook()
        await dp.storage.close()
        await dp.storage.wait_closed()

    if __name__ == '__main__':
        # dp.middleware.setup(MidlWare())
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )   
        