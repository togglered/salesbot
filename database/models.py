from sqlalchemy import String, Integer, Table, ForeignKey, Column
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


engine = create_async_engine(url = 'sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass


user_products = Table(
    "user_products",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    products: Mapped[list["Product"]] = relationship(
        "Product",
        secondary=user_products,
        back_populates="users"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[int] = mapped_column(Integer)
    description_path: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_products,
        back_populates="products"
    )


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
