from aiogram import F, Router, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.requests import get_all_products, add_product, get_product
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from forms import ProductState


router = Router()

carts = {}

@router.message(F.text == "/start")
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Каталог 📜", callback_data="catalog_0")]
        ]
    )
    await message.answer("👋 Привет, добро пожаловать в наш магазин.\n\n"\
                       "Чтобы просмотреть наш каталог товаров нажмите на кнопку ниже:⬇️", reply_markup=keyboard)



@router.callback_query(F.data.startswith("catalog_"))
async def show_catalog(callback: CallbackQuery):
    products = await get_all_products()
    page = int(callback.data.split("_")[1])
    if not products:
        await callback.message.edit_text("Каталог на данный момент пуст.")
        return

    if page < 0 or page >= len(products):
        await callback.answer("Больше товаров нет")
        return

    product = products[page]
    text = (
                f"<b>{product.name}</b>\n"
                f"Цена: {product.price}: {product.currency}\n\n"
                f"Описание:\n{product.description}"
            )

    nav_row = []

    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"catalog_{page - 1}"))

    if page < len(products) - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog_{page + 1}"))



    rows = []
    if nav_row:
        rows.append(nav_row)
    rows.append(
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_cart_{product.id}")]
    )
    kb_for_cart = InlineKeyboardMarkup(inline_keyboard=rows)


    await callback.message.delete()

    if product.photo:
        await callback.message.answer_photo(
        photo=product.photo,
        caption=text,
        parse_mode="HTML",
        reply_markup=kb_for_cart
    )
    else:
        await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb_for_cart
    )

    await callback.answer()



@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    carts[user_id].append(product_id)
    print(carts[user_id])
    await callback.answer("✅ Товаp был успешно добавлен в корзину.")



@router.message(F.text == "/cart")
async def show_cart(message: Message):
    user_id = message.from_user.id

    if user_id not in carts or not carts[user_id]:
        await message.answer("Корзина пуста.")
        return

    text = "🛒 Ваша корзина:\n\n"
    total = 0
    for product_id in carts[user_id]:
        product = await get_product(product_id)
        if product:
            text += f"{product.name} - {product.price} {product.currency}\n"
            total += product.price

    text += f"\nИтого: {total}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💲 Оформить заказ", callback_data="checkout")]
        ]
    )

    await message.answer(text, reply_markup=keyboard) 



@router.callback_query(F.data == "checkout")
async def checkout_handler(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if user_id not in carts or not carts[user_id]:
        await callback.message.edit_text("Ваша корзина ещё пустая.\nДобавьте товар в корзину чтобы оформить заказ.")
        return
    else:
        user = callback.from_user
        username = f"@{user.username}" if user.username else "нет"
        text_for_admin = "🔔Новый заказ\n"\
                        f"От: Имя:{user.first_name} / {username} / ID:{user.id}\n"\
                        "Товары:"

        total = 0
        for product_id in carts[user_id]:
            product = await get_product(product_id)
            if product:
                text_for_admin += f"{product.name} - {product.price} {product.currency}\n"
                total += product.price

        text_for_admin += f"\nИтого: {total}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять заказ", callback_data=f"accept_order_{user_id}")],
            [InlineKeyboardButton(text="❌ Отклонить заказ", callback_data=f"reject_order_{user_id}")]
        ]
    )
    await bot.send_message(ADMIN_ID, text_for_admin, reply_markup=kb)
    await bot.send_message(user_id, "Заказ отправлен. Ожидайте подтверждения.")

    await callback.answer()  

        


@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[-1])
    await bot.send_message(user_id, "✅ Ваш заказ был принят, с вами скоро свяжуться.")
    carts[user_id] = []
    await callback.message.edit_text(
    callback.message.text + "\n\n✅ Принято"
    )
    await callback.answer()



@router.callback_query(F.data.startswith("reject_order_"))
async def accept_order(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[-1])
    await bot.send_message(user_id, "❌ Ваш закз не был принят.")
    carts[user_id] = []
    await callback.message.edit_text(
    callback.message.text + "\n\n❌ Отклонено"
    )
    await callback.answer()
    




@router.message(F.text == "/add_product")
async def add_product_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только админам.")
        return
    else:
        await state.set_state(ProductState.name)
        await message.answer("Введите название товара:")


@router.message(ProductState.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(ProductState.description)
    await message.answer("Введите описание товара:")



@router.message(ProductState.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProductState.price)
    await message.answer("Введите цену товара (только число):")


@router.message(ProductState.price)
async def process_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите цену числом, пожалуйста.")
        return


    text = message.text.replace(" ", "").replace(",", ".")
    parts = text.split(".")
    if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
        text = parts[0] + parts[1]


    try:
        price = float(text)
    except ValueError:
        await message.answer("Введите, пожалуйста, число.")
        return

    await state.update_data(price=price)
    await state.set_state(ProductState.currency)
    
    
    currencies = ["EUR", "USD", "UAH", "PLN", "RUB"]

    buttons = [
    [InlineKeyboardButton(text=cur, callback_data=f"currency_{cur}")]
    for cur in currencies
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "Выберите валюту:",
        reply_markup=keyboard
    )



@router.callback_query(F.data.startswith("currency_"))
async def curency_choosing(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.removeprefix("currency_")
    await state.update_data(currency=currency)
    
    await state.set_state(ProductState.photo)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_photo")]
        ]
    )

    await callback.message.edit_text(
        f"Валюта: {currency}\n\nПришлите фото товара или нажмите «Пропустить»:",
        reply_markup=keyboard
    )
    await callback.answer()





@router.callback_query(F.data == "skip_photo", ProductState.photo)
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    data = await state.get_data()

    await add_product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        currency=data["currency"],
        photo=None
    )

    await state.clear()
    await callback.message.edit_text("Товар успешно добавлен!")
    await callback.answer()



@router.message(ProductState.photo)
async def process_photo(message: Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1].file_id
    else:
        photo = None

    await state.update_data(photo=photo)

    data = await state.get_data()

    await add_product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        currency=data["currency"],
        photo=data["photo"]
    )

    await state.clear()
    await message.answer("Товар успешно добавлен:)")


@router.callback_query(F.data == "catalog")
async def show_catalog_command(callback: CallbackQuery):
    catalog = await get_all_products()

    if not catalog:
        await callback.message.edit_text("К сожалению каталог пока пуст.")
    else:
        await callback.message.edit_text("Вот весь каталог:")

    await callback.answer()