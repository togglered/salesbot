from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Product


main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ДОБАВИТЬ ТОВАР", callback_data="add_product")],
    [InlineKeyboardButton(text="УДАЛИТЬ ТОВАР", callback_data="choose_product_to_delete")]
])

def products_to_delete(products: list[Product]):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"УДАЛИТЬ '{product.name}'", callback_data=f"delete_product:{product.id}")]
        for product in products
    ])