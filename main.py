from aiogram import Bot, Dispatcher
from logging import basicConfig, INFO
import asyncio
from handlers.routes import router
from middleware.rate_limit import RateLimitMiddleware
from database.engine import init_db
from config import BOT_TOKEN
from aiogram.types import BotCommand


bot = Bot(token=BOT_TOKEN)

basicConfig(level=INFO)

async def main():

    dp = Dispatcher()

    await init_db()

    dp.message.middleware(RateLimitMiddleware(limit_seconds=1.0))
    dp.callback_query.middleware(RateLimitMiddleware(limit_seconds=1.0))

    dp.include_router(router)

    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="cart", description="Корзина"),
        BotCommand(command="add_product", description="Добавить продукт")
    ]
    await bot.set_my_commands(commands)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
