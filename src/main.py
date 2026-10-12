import asyncio
import logging
from aiogram import Bot, Dispatcher
from src.config import settings
from src.database import init_db
from src.handlers import router

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    init_db()
    
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Сбрасываем старый вебхук и зависшие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("Бот успешно запущен и ожидает входящих сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())