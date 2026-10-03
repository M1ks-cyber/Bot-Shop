from aiogram.fsm.state import StatesGroup, State


class ProductState(StatesGroup):
    name = State()
    description = State()
    price = State()
    currency = State()
    photo = State()