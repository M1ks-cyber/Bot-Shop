from aiogram import BaseMiddleware
import time


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit_seconds: float = 1.0):
        self.limit_seconds = limit_seconds
        self.user_timestamps = {}


    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        user_id = user.id

        current_time = time.time()

        last_time = self.user_timestamps.get(user_id, 0)

        if current_time - last_time < self.limit_seconds:
            await event.answer(f"Wait a little, sending a message is avaible every {self.limit_seconds} seconds")
            return

        self.user_timestamps[user_id] = current_time

        return await handler(event, data)