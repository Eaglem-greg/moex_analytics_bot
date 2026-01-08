<<<<<<< HEAD
=======
import asyncio
import logging
from config.config import Config, load_config
from handlers.quote import quote_router
from handlers.start import start_router
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand


logger = logging.getLogger(__name__)


async def main()->None:
    config: Config = load_config()
    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format,
    )

    bot = Bot(config.bot.token)
    dp=Dispatcher()
    
    #Создание кнопки Меню
    main_menu_commands=[
        BotCommand(command="/help", description="Справка о работе бота"),
        BotCommand(command="/start", description="Запуск бота"),
        BotCommand(command="/quote", description="Выбор необходимого тикера")
    ]
    await bot.set_my_commands(main_menu_commands)

    #Подключение роутеров
    dp.include_router(quote_router)
    dp.include_router(start_router)


    await dp.start_polling(bot)

asyncio.run(main())

>>>>>>> 45dd776a9dd0cd2891d395f848be087a96b7954d
