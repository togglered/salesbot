from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
import os
import shutil

import keyboards.admin as kb
from database.models import async_session, Product
from app_config.logger_config import logger
from app_config import CONFIG

admin_router = Router()

class CreateProduct(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_price = State()
    waiting_for_product_desription = State()
    waiting_for_product_file = State()


@admin_router.message(Command('admin'))
async def admin_panel(message: Message):
    if message.from_user.id == CONFIG['ADMIN_ID']:
        await message.reply("АДМИНКА", reply_markup=kb.main)


@admin_router.callback_query(F.data == ('add_product'))
async def add_product(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.from_user.id == CONFIG['ADMIN_ID']:
        await callback.message.answer("Введите имя товара:")
        await state.set_state(CreateProduct.waiting_for_product_name)


@admin_router.message(CreateProduct.waiting_for_product_name)
async def process_product_name(message: Message, state: FSMContext):
    if message.from_user.id == CONFIG['ADMIN_ID']:
        await state.update_data(product_name=message.text)
        await message.answer("Введите цену товара в рублях:")
        await state.set_state(CreateProduct.waiting_for_product_price)


@admin_router.message(CreateProduct.waiting_for_product_price)
async def process_product_price(message: Message, state: FSMContext):
    if message.from_user.id == CONFIG['ADMIN_ID']:
        await state.update_data(product_price=message.text)
        await message.answer("Пришлите описание товара:")
        await state.set_state(CreateProduct.waiting_for_product_desription)


@admin_router.message(CreateProduct.waiting_for_product_desription)
async def process_product_description(message: Message, state: FSMContext):
    if message.from_user.id == CONFIG['ADMIN_ID']:
        await state.update_data(product_description=message.text)
        await message.answer("Пришлите файл товара:")
        await state.set_state(CreateProduct.waiting_for_product_file)


@admin_router.message(CreateProduct.waiting_for_product_file)
async def process_product_file(message: Message, state: FSMContext):
    if message.from_user.id == CONFIG['ADMIN_ID']:
        await state.update_data(product_file=message.document)
        data = await state.get_data()
        product_name = data["product_name"]
        product_price = data["product_price"]
        product_description = data["product_description"]
        product_file = data["product_file"]

        if not os.path.exists(f'products/{product_name}'):
            os.makedirs(f'products/{product_name}')

        with open(f'products/{product_name}/description.txt', 'w+', encoding='utf-8') as description_file:
            description_file.write(product_description)

        bot = message.bot

        file = await bot.get_file(product_file.file_id)
        await bot.download_file(file.file_path, destination=f"products/{product_name}/prog.zip")

        async with async_session() as session:
            session.add(Product(
                name=product_name,
                price=product_price,
                description_path=f'products/{product_name}/description.txt',
                file_path=f"products/{product_name}/prog.zip"
                ))
            await session.commit()

        logger.info(f"Product {product_name} has been added.")
        await message.answer(f"Товар добавлен: {product_name} за {product_price} рублей")

        await state.clear()


@admin_router.callback_query(F.data == ('choose_product_to_delete'))
async def choose_product_to_delete(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id == CONFIG['ADMIN_ID']:
        async with async_session() as session:
            products = (await session.scalars(select(Product))).all()
            if products:
                await callback.message.answer(f"Выбери товар, который необходимо удалить:", reply_markup=kb.products_to_delete(products))
            else:
                await callback.message.answer(f"У тебя нет никаких товаров!")


@admin_router.callback_query(F.data.startswith('delete_product'))
async def delete_product(callback: CallbackQuery):
    await callback.answer()
    product_id = callback.data.split(':')[1]

    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))

        if os.path.exists(f"products/{product.name}"):
            shutil.rmtree(f"products/{product.name}")

        await session.delete(product)
        await session.commit()

    logger.info(f"Product {product.name} has been deleted.")
    await callback.message.answer(f"Товар {product.name} удален!")



