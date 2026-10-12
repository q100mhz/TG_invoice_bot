import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnector
from src.config import settings
from src.database import init_db
from src.handlers import router

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    init_db()
    
    session = None
    if settings.proxy_url:
        logging.info(f"Инициализация подключения через прокси: {settings.proxy_url}")
        connector = ProxyConnector.from_url(settings.proxy_url)
        session = AiohttpSession(connector=connector)
        bot = Bot(token=settings.bot_token, session=session)
    else:
        bot = Bot(token=settings.bot_token)

    dp = Dispatcher()
    dp.include_router(router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Бот успешно подключился к Telegram и ожидает сообщений!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())