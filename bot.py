from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import os.path
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.dispatcher.handler import CancelHandler
import conf
# from aiogram.dispatcher.middlewares import BaseMiddleware
from loguru import logger
from aiogram.utils.executor import start_webhook
from bd.bd import BotBD
import datetime
import localization
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

TEST_MODE = True

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
botBD = BotBD()

logger.add("debug.txt")
# webhook settings
WEBHOOK_HOST = 'https://zelse.asuscomm.com'
WEBHOOK_PATH = '/prod_chbeads'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '0.0.0.0'  # or ip 127.0.0.1
WEBAPP_PORT = 3010


# -----------------ststes-------------------------------
class FSMSendPhoto(StatesGroup):
    photo = State()

# ----------------клавіатури----------------------------
kbcl = ReplyKeyboardMarkup(resize_keyboard=True)
kbcl.add('Отримати реквізити💳')
kbkv = ReplyKeyboardMarkup(resize_keyboard=True)
kbkv.add('Надіслати квитанцію🧾')


# -------------------functions--------------------------------------
def userAccess(id):
    try:
        curentDate = botBD.getUserCurentDay(id)
        dateNow = datetime.datetime.now()
        datenow = dateNow.strftime("%Y-%m-%d")
        countOfRequest = botBD.getRequestCount(id)
        paymentStatus = botBD.getUserPaymentStatus(id)


        if paymentStatus == "yes":
            return True

        if curentDate != datenow:
            botBD.setUserCurentDay(id, datenow)
            botBD.setUserCountOfDay(id, 0)

        if countOfRequest >= 300:  # початковий ліміт на кількість
            countOfDayRequests = botBD.getRequestCountOfDay(id)
            if countOfDayRequests < 5:
                botBD.incrementUserRequestCountOfDay(id)
                return True
            else:
                return False  # перевершив денний ліміт
        else:
            return True

    except IndexError:
        logger.debug(f"Index error {id} ")

    except Exception as e:
       
        logger.debug(f"Виникла помилка: {e}")


def loc(id, str):
    # language = botBD.getUserLocalization(id)
    # for index, value in localization.UA.items():
    #     if str == value:
    #         break
    # if language == "UA":
    #     return localization.UA[index]
    # else:
    #     return localization.EN[index]
    return str


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
@dp.message_handler(commands=['start'], state=None)
async def send_welcome(message: types.Message):
    await message.reply(loc(message.from_user.id,
                            "Вітаю! В моїй базі є понад 1100 зображень чеського бісеру! Введіть код бісеру тут👇, а я відправлю вам його зображення!"))
    if botBD.is_subscriber_exists(message.from_user.id) == False:
        botBD.add_subscriber(message.from_user.id)
        await bot.send_message(1080587853,
                               f"Новенький підписався {message.from_user.first_name} - {message.from_user.id}")

        logger.debug(f"Новенький {message.from_user.first_name} - {message.from_user.id} підписався")


@dp.message_handler(commands=['help'], state=None)
async def help(message: types.Message):
    await message.reply('Даний функціонал ще в розробці')


@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def handle_file(message: types.Message):
    await message.photo[-1].download(f'invoice/{message.from_user.id}.jpg')
    doc = open(f'invoice/{message.from_user.id}.jpg', 'rb')
    await bot.send_message(1080587853,
                           f"Користувач {message.from_user.first_name} - {message.from_user.id} надіслав файл. Для активації профілю #{message.from_user.id}")
    await bot.send_photo(1080587853, doc)
    await message.answer(f"Дякуємо! Файл отримано!")
    logger.info(f"Користувач {message.from_user.id} надіслав файл")


@dp.message_handler(content_types=[types.ContentType.DOCUMENT])
async def handle_file(message: types.Message):
    document = message.document
    file_name = document.file_name
    file_path = f'invoice/{message.from_user.id}{file_name}'
    await document.download(file_path)
    await bot.send_message(1080587853,
                           f"Користувач {message.from_user.first_name} - {message.from_user.id} надіслав файл. Для активації профілю #{message.from_user.id}")
    with open(file_path, 'rb') as document_file:
        await bot.send_document(chat_id=1080587853, document=document_file)
    await message.answer(f"Дякуємо! Файл отримано! Активація профілю на протязі 24 год.")
    logger.info(f"Користувач {message.from_user.id} надіслав файл {file_name}")


##----------------------------Різне----------------------##
@dp.message_handler()
async def echo(message: types.Message):
    if botBD.is_subscriber_exists(message.from_user.id) == False:
        botBD.add_subscriber(message.from_user.id)
        await bot.send_message(1080587853,
                               f"Новенький підписався {message.from_user.first_name} - {message.from_user.id}")

        logger.debug(f"Новенький {message.from_user.first_name} - {message.from_user.id} підписався")

    userId = message.from_user.id
    logger.debug(f'User {message.from_user.first_name}-{userId} type {message.text}')

    if message.text == "Файл12" and userId in conf.ADMIN_ID:
        doc = open('debug.txt', 'rb')
        await message.reply_document(doc)

    elif message.text.startswith("#") and userId in conf.ADMIN_ID:
        id = message.text[1:]
        botBD.setUserPaymentStatus(id, "yes")
        status = botBD.getUserPaymentStatus(id)
        if status == "yes":
            await message.answer(f"Профіль активовано")
            await bot.send_message(id, f"Безліміт активовано!")


    elif message.text == "Стат" and userId in conf.ADMIN_ID:
        await message.answer(f"Ось статистика:\nКористувачів ботом - {botBD.usersCount()}\n{botBD.getAllUsers()}")

    elif message.text == "Отримати реквізити💳":
        await message.answer(
            f"Приват 4149439046626911\nЗелінська Ю.В.\nПісля оплати ОБОВЯЗКОВО надішліть в боті квитанцію.",
            reply_markup=kbkv)
    elif message.text == "Надіслати квитанцію🧾":
        await message.answer(
            f"Прикріпіть файл із квитанцією на надішліть в боті.", reply_markup=types.ReplyKeyboardRemove())


    elif message.text.isdigit():
        if len(message.text) == 5:
            if userAccess(message.from_user.id):
                check_file = os.path.exists(f'biser_pic/c{message.text}.jpg')
                if check_file:
                    doc = open(f'biser_pic/c{message.text}.jpg', 'rb')
                    await message.reply_photo(doc)
                    botBD.incrementUserRequestCount(userId)
                else:
                    await message.answer(loc(userId, "Нажаль такого бісеру немає в моїй базі даних!"))
            else:
                await message.answer(loc(userId,
                                         "Ви використали ліміт в 5 запитів на день! Якщо ви бажаєте забрати ліміт оплатіть одноразову підписку в розмірі 350грн та надішліть квитанцію про оплату."),
                                     reply_markup=kbcl)

        else:
            await message.answer(loc(userId, "Коди чеського бісеру 5ти значні!"))
    else:
        await message.answer(loc(userId, "Будь - ласка введіть код бісеру👇. Наприклад 97070"))


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
