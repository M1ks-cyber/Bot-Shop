from sqlalchemy import BigInteger, String, Integer, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(900), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    photo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)