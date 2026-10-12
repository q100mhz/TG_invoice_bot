import asyncio
import logging
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from src.config import settings
from src.database import init_db
from src.handlers import router

class CustomSocksSession(AiohttpSession):
    def __init__(self, proxy_url: str, **kwargs):
        super().__init__(**kwargs)
        self.proxy_url = proxy_url

    async def create_session(self) -> ClientSession:
        connector = ProxyConnector.from_url(self.proxy_url)
        return ClientSession(connector=connector, json_serialize=self.json_dumps)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    init_db()
    
    # Подключаемся к локальному контейнеру Tor
    proxy_url = settings.proxy_url or "socks5://tor:9050"
    logging.info(f"Инициализация подключения через: {proxy_url}")
    session = CustomSocksSession(proxy_url=proxy_url)
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