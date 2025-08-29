from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from payment import PaymentMethod
from database.models import Product


main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛍️ Товары", callback_data="display_products"),
     InlineKeyboardButton(text="🛒 Мои покупки", callback_data="display_purchases")],
])

return_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏚 Главное меню", callback_data=f"main_menu")]
])

cancel_payment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отменить оплату", callback_data=f"main_menu")]
])

def get_file(product: Product):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Скачать архив", callback_data=f"download:{product.id}")],
        [InlineKeyboardButton(text="🏚 Главное меню", callback_data=f"main_menu")]
    ])

async def get_payment_methods(product: Product, payment_methods: list[PaymentMethod]):
    if len(payment_methods) <= 6:
        keyboard = [
            [InlineKeyboardButton(text=method.name, callback_data=f"pay:{method.name}:{product.id}")] for method in payment_methods
        ]
    else:
        columns = 3
        keyboard = []
        i = 0
        while i < len(payment_methods) - 1:
            keyboard.append([])
            for j in range(columns):
                if i < len(payment_methods):
                    keyboard[i // columns].append(InlineKeyboardButton(text=payment_methods[i].name, callback_data=f"pay:{payment_methods[i].name}:{product.id}"))
                else:
                    keyboard[i // columns].append(InlineKeyboardButton(text="\u200b", callback_data="None"))
                i += 1
    keyboard.append([InlineKeyboardButton(text="🏚 Главное меню", callback_data=f"main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def buy_product(product: Product):
    keyboard = [
        [InlineKeyboardButton(text=f"💸 Купить - {product.price} рублей", callback_data=f"buy_product:{product.id}")],
        [InlineKeyboardButton(text="🏚 Главное меню", callback_data=f"main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def buy_products(products: list[Product] = []):
    keyboard = [
        [InlineKeyboardButton(text=f"{product.name} - {product.price} рублей", callback_data=f"product_info:{product.id}")]
        for product in products
    ]
    keyboard.append(
        [InlineKeyboardButton(text="🏚 Главное меню", callback_data=f"main_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)