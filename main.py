import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, GPT_TOKEN
from aiogram.client.default import DefaultBotProperties
from bot.middlewares.session import DataBaseSession
from bot.handlers.main_handlers import router as main_router
from bot.handlers.comp_handlers import router as comp_router
from bot.handlers.ask_handlers import router as ask_router
from database.engine import async_session
from openai import AsyncOpenAI


dp = Dispatcher()

async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    
    dp.update.middleware(DataBaseSession(session_pool=async_session))
    
    dp.include_router(main_router)
    dp.include_router(comp_router)
    dp.include_router(ask_router)
    
    async def on_shutdown() -> None:
        await bot.session.close() 
    
    await dp.start_polling(bot, shutdown=on_shutdown)
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass