from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_keyboards import main_reply_kb

from database.user import register_user, check_active_subscription, check_has_energy


router = Router()


@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    
    tg_user = msg.from_user
    user_id = tg_user.id
    username = tg_user.username or tg_user.full_name

    # регистрируем или узнаём что уже был в БД
    is_new = await register_user(session, user_id, username)

    if is_new:
        await msg.answer(text = 
                         """Привет! Я сделаю для тебя расклад и прогноз на любой вопрос!
                         
Напиши какой вопрос ты задаёшь для расклада.
Ты можешь выбрать карты в боте, либо написать свои карты через запятую, если у тебя на руках физическая колода!

Пример вопроса:
Буду ли я встречаться с Артёмом?
Пример расклада:
Влюбленные, справедливость, 6 мечей.

P.S. Если бот сломался, попробуйте написать /start
Кнопка меню находится снизу рядом с полем куда писать текст.""",
                        reply_markup=main_reply_kb)
    else:
        await msg.answer(f"""👋 С возвращением, {username}!Я сделаю для тебя расклад и прогноз на любой вопрос!
                         
Напиши какой вопрос ты задаёшь для расклада.
Ты можешь выбрать карты в боте, либо написать свои карты через запятую, если у тебя на руках физическая колода!

Пример вопроса:
Буду ли я встречаться с Артёмом?
Пример расклада:
Влюбленные, справедливость, 6 мечей.

P.S. Если бот сломался, попробуйте написать /start
Кнопка меню находится снизу рядом с полем куда писать текст.""",
                        reply_markup=main_reply_kb)
        

@router.message(F.text == "Задать вопрос")
async def send_quest(msg: Message, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id):
        await msg.answer(text="Подписка активна")
    else:
        await msg.answer(text="Нет подписки")
    
    if await check_has_energy(session, msg.from_user.id):
        await msg.answer(text="Энергия есть")
    else:
        await msg.answer(text="Энергия закончилась")
    


@router.message(F.text == "Получить расклады")
async def get_cards(msg: Message, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id):
        await msg.answer(text="Подписка активна")
    else:
        await msg.answer(text="Нет подписки")
    
    if await check_has_energy(session, msg.from_user.id):
        await msg.answer(text="Энергия есть")
    else:
        await msg.answer(text="Энергия закончилась")


@router.message(F.text == "Как работает бот")
async def get_info(msg: Message, session: AsyncSession) -> None:
    await msg.answer(text="""Здесь будет подробное описание""")