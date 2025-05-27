from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.user import register_user, check_active_subscription, check_has_energy
from bot.keyboards.comp_keyboards import q1_markup, q2_markup, q3_markup, comp_prompt

import openai
from openai import AsyncOpenAI
from config import GPT_TOKEN

router = Router()

class CheckComp(StatesGroup):
    ask_names_dates = State()
    quest1 = State()
    quest2 = State()
    quest3 = State()
    

@router.message(F.text == "Проверить совместимость")
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id):
        await msg.answer(text="""Привет! Хочешь понять, насколько вы подходите друг другу?  
💞 Просто напиши имена и даты рождения — я проверю вашу совместимость по Матрице Судьбы.""")
        
        await state.set_state(CheckComp.ask_names_dates)
        
    else:
        await msg.answer(text="Нет подписки")
        

@router.message(CheckComp.ask_names_dates)
async def ask_quest(msg: Message, state: FSMContext):
    pair_info = msg.text
    await state.update_data(pair_info = pair_info)
    await msg.answer(text="Как вы сейчас общаетесь?",
                     reply_markup=q1_markup)
    await state.set_state(CheckComp.quest1)
    
    
@router.message(CheckComp.quest1)
async def ask_quest(msg: Message, state: FSMContext):
    ans1 = msg.text
    await state.update_data(ans1 = ans1)
    await msg.answer(text="Что тебя больше всего интересует?",
                     reply_markup=q2_markup)
    await state.set_state(CheckComp.quest2)
    

@router.message(CheckComp.quest2)
async def ask_quest(msg: Message, state: FSMContext):
    ans2 = msg.text
    await state.update_data(ans2 = ans2)
    await msg.answer(text="Что ты сейчас чувствуешь по поводу этих отношений?",
                     reply_markup=q3_markup)
    await state.set_state(CheckComp.quest3)
    
    
@router.message(CheckComp.quest3)
async def ask_quest(msg: Message, state: FSMContext):
    ans3 = msg.text
    data = await state.get_data()
    ans1 = data.get('ans1')
    ans2 = data.get('ans2')
    pair_info = data.get('pair_info')
    
    try:
        client = AsyncOpenAI(api_key=GPT_TOKEN)
        response = await client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[
                {"role": "system", "content": comp_prompt},
                {"role": "user",   "content": (
                    f"Информация о паре: {pair_info}\n"
                    f"Ответ1: {ans1}\n"
                    f"Ответ2: {ans2}\n"
                    f"Ответ3: {ans3}"
                )}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        await msg.answer(response.choices[0].message.content.strip())
        await state.clear()
    
    except Exception as e:
        print(e)
        await msg.answer("Кажется, неполадки с космосом, подождем, когда пройдет ретроградный Меркурий")
        await state.clear()
    