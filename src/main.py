import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from src.config import settings
from src.database import init_db
from src.handlers import router

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    init_db()
    
    # Подключаемся к локальному HTTP-прокси Tor без сторонних коннекторов
    proxy_url = settings.proxy_url or "http://tor:8118"
    logging.info(f"Инициализация сессии через HTTP-прокси: {proxy_url}")
    
    session = AiohttpSession(proxy=proxy_url)
    bot = Bot(token=settings.bot_token, session=session)

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