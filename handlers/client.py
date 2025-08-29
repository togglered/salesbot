from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio

import keyboards.client as kb
from payment import PaymentMethod
from database.models import async_session, User, Product
from app_config.logger_config import logger
from app_config import CONFIG
from utils import get_all_subclasses


client_router = Router()

tasks = {}

@client_router.callback_query(F.data == "None")
async def none_callback(callback: CallbackQuery):
    await callback.answer()
    

@client_router.message(CommandStart())
async def start_message(message: Message):
    id = message.from_user.id
    if id in tasks.keys():
        tasks[id].cancel()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == id))
        if not user:
            session.add(User(id=id))
            await session.commit()
    
    member = await message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        await message.answer(f"Добро пожаловать, {message.from_user.first_name}!", reply_markup=kb.main)
    else:
        await message.answer(f"Добро пожаловать, {message.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")


@client_router.callback_query(F.data == "main_menu")
async def start_callback(callback: CallbackQuery):
    await callback.message.delete()
    id = callback.from_user.id
    if id in tasks.keys():
        tasks[id].cancel()
    member = await callback.message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.id == id))
            if not user:
                session.add(User(id=id))
                await session.commit()
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}!", reply_markup=kb.main)
        await callback.answer()
    else:
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")
    

@client_router.callback_query(F.data == ('display_products'))
async def display_products(callback: CallbackQuery):
    await callback.message.delete()
    id = callback.from_user.id
    member = await callback.message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        async with async_session() as session:
            products = (await session.scalars(select(Product))).all()
        await callback.message.answer("💰 Наши товары:", reply_markup=kb.buy_products(products))
        await callback.answer()
    else:
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")


@client_router.callback_query(F.data == ('display_purchases'))
async def display_purchases(callback: CallbackQuery):
    await callback.message.delete()
    id = callback.from_user.id
    member = await callback.message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        async with async_session() as session:
            user = await session.scalar(
                select(User).options(selectinload(User.products)).where(User.id == callback.from_user.id)
            )
            if user.products:
                await callback.message.answer("💵 Твои покупки:", reply_markup=kb.buy_products(user.products))
            else:
                await callback.message.answer("Ты пока что ничего не купил!", reply_markup=kb.return_to_main_menu)
        await callback.answer()
    else:
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")


@client_router.callback_query(F.data.startswith('product_info'))
async def product_info(callback: CallbackQuery):
    await callback.message.delete()
    id = callback.from_user.id
    member = await callback.message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        product_id = callback.data.split(':')[1]

        async with async_session() as session:
            product = await session.scalar(select(Product).where(Product.id == product_id))
            user = await session.scalar(
                select(User).options(selectinload(User.products)).where(User.id == callback.from_user.id)
            )
        
            with open(f"products/{product.name}/description.txt", 'r', encoding='utf-8') as description_file:
                if product in user.products:
                    await callback.message.answer(description_file.read(), reply_markup=kb.get_file(product))
                else:
                    await callback.message.answer(description_file.read(), reply_markup=kb.buy_product(product))
        await callback.answer()
    else:
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")


@client_router.callback_query(F.data.startswith("download"))
async def download(callback: CallbackQuery):
    id = callback.from_user.id
    member = await callback.message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        product_id = callback.data.split(':')[1]

        async with async_session() as session:
            product = await session.scalar(select(Product).where(Product.id == product_id))
            user = await session.scalar(
                select(User).options(selectinload(User.products)).where(User.id == callback.from_user.id)
            )
        
            if product in user.products:
                await callback.message.answer_document(FSInputFile(f'products/{product.name}/prog.zip'))
        await callback.answer()
    else:
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")


@client_router.callback_query(F.data.startswith('buy_product'))
async def buy_product(callback: CallbackQuery):
    await callback.message.delete()
    id = callback.from_user.id
    member = await callback.message.bot.get_chat_member(CONFIG["CHANNEL_ID"], id)
    if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR):
        product_id = callback.data.split(':')[1]

        async with async_session() as session:
            product = await session.scalar(select(Product).where(Product.id == product_id))
            user = await session.scalar(
                select(User).options(selectinload(User.products)).where(User.id == callback.from_user.id)
            )
            if not product in user.products:
                await callback.message.answer("💰 Выбери способ оплаты:", reply_markup=await kb.get_payment_methods(product=product, payment_methods=PaymentMethod.__subclasses__()))
        await callback.answer()
    else:
        await callback.message.answer(f"Добро пожаловать, {callback.from_user.first_name}! Чтобы пользоваться ботом, необходимо подписаться на канал: {CONFIG['CHANNEL_USERNAME']}")


@client_router.callback_query(F.data.startswith('pay'))
async def pay(callback: CallbackQuery):
    await callback.message.delete()
    payment_method_name = callback.data.split(':')[1]
    product_id = callback.data.split(':')[2]
    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
    for payment_method in PaymentMethod.__subclasses__():
        if payment_method.name == payment_method_name:
            if payment_method.__subclasses__():
                await callback.message.answer("💰 Выбери способ оплаты:", reply_markup=await kb.get_payment_methods(product=product, payment_methods=payment_method.__subclasses__()))
                return
    tasks[callback.from_user.id] = asyncio.create_task(process_payment(callback))
    


async def process_payment(callback: CallbackQuery):
    await callback.answer()
    payment_method_name = callback.data.split(':')[1]
    product_id = callback.data.split(':')[2]
    user_id = callback.from_user.id
    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        user = await session.scalar(
            select(User).options(selectinload(User.products)).where(User.id == user_id)
        )
        if not product in user.products:
            for payment_method in get_all_subclasses(PaymentMethod):
                if payment_method.name == payment_method_name:
                    payment = payment_method(product=product, user=user)
                    payment_message = await payment.get_payment_message()
                    msg = await callback.message.answer(payment_message, reply_markup=kb.cancel_payment)
                    for _ in range(payment.PAYMENT_ATTEMPS):
                        paid = await payment.check_payment()
                        if paid:
                            await msg.delete()
                            logger.info(f"User {callback.from_user.full_name} has bought {product.name}: {product.price}")
                            await callback.message.answer("✅ Оплата прошла успешно! Скачать товар можно, по кнопке ⬇️ или во вкладке 🛒 Мои покупки!", reply_markup=kb.get_file(product))

                            user.products.append(product)
                            await session.commit()

                            return True
                        
                        await asyncio.sleep(payment.PAYMENT_ATTMEP_DELAY)

                    await msg.delete()
                    await callback.message.answer("⚠️ Не смогли найти твою оплату!", reply_markup=kb.return_to_main_menu)
    