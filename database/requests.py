from sqlalchemy import select
from database.engine import async_session
from database.models import Product


async def add_product(name: str, description: str, price: float, currency: str, photo: str | None = None):
    async with async_session() as session:
        session.add(Product(
            name=name,
            description=description,
            price=price,
            currency=currency,
            photo=photo
        ))
        await session.commit()



async def get_all_products():
    async with async_session() as session:
        products = await session.scalars(select(Product).where(Product.is_active == True))
        return products.all()



async def get_product(id: int):
    async with async_session() as session:
        res = await session.scalar(select(Product).where(Product.id == id))
        return res