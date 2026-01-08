from aiogram import Router, types
from aiogram.filters import Command
import logging
from lexicon.lexicon import LEXICON_RU

start_router = Router()

logger = logging.getLogger(__name__)

@start_router.message(Command("start"))
async def process_start_command(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer(LEXICON_RU['start'])

@start_router.message(Command("help"))
async def process_help_command(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} вызвал \help")
    txt_answer = LEXICON_RU['help']
    await message.answer(txt_answer)

