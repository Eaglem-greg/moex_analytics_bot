import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.config import Config, load_config
from aiogram.client.default import DefaultBotProperties
from handlers.quote import quote_router
from handlers.start import start_router 
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)

async def main():
    config: Config = load_config()
    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format
    )

    logger.info("start bot")

    bot=Bot(token=config.bot.token,
            default=DefaultBotProperties)
    dp = Dispatcher()

    main_menu_command = [
        BotCommand(command="/start",
                   description="Запуск бота"),
        BotCommand(command="/help",
                   description="Список всех команд"),
        BotCommand(command="/quote",
                   description="Выбор тикера")
    ]
    await bot.set_my_commands(main_menu_command)

    dp.include_router(quote_router)
    dp.include_router(start_router)
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
