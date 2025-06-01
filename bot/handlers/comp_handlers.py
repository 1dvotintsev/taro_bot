from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.user import check_active_subscription, check_has_energy
from bot.keyboards.comp_keyboards import q1_markup, q2_markup, q3_markup, comp_prompt, continue_markup, comp_pair_btn
from bot.keyboards.main_keyboards import energy_button

from openai import AsyncOpenAI
from config import GPT_TOKEN

router = Router()
client = AsyncOpenAI(api_key=GPT_TOKEN)

class CheckComp(StatesGroup):
    ask_names_dates = State()
    quest1 = State()
    quest2 = State()
    quest3 = State()
    

@router.message((F.text == "💞Проверить совместимость💞") | (F.text == "💌 Еще одна проверка совместимости"))
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await state.clear()
    if (await check_active_subscription(session, msg.from_user.id)) or (await check_has_energy(session, msg.from_user.id)):
        await msg.answer(text="""Насколько вы подходите друг другу?
                         
💞 Напиши мне имена и даты рождения вашей пары — я проверю совместимость по Матрице Судьбы.

❗️ Всё в одном сообщении, в таком  формате:
Анна 14.02.2001
Дмитрий 24.07.2001""")
        
        await state.set_state(CheckComp.ask_names_dates)
        
    else:
        await msg.answer(text="""❤️‍🔥 Ты уже сделала максимум бесплатных разборов и проверок 💔
                         
Но ты можешь
                         
🔮 Открыть полный доступ - и задавать столько вопросов и  делать столько проверок совместимости, сколько нужно""",
                     reply_markup=energy_button)
        
        
@router.message(F.text == "💘 Проверить совместимость")
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    if (await check_active_subscription(session, msg.from_user.id)) or (await check_has_energy(session, msg.from_user.id)):
        data = await state.get_data()
        
        if 'pair_info' in data:
            pair_info = data['pair_info']
            await msg.answer(text=f"Готовим ответ по этой паре?\n\n{pair_info}",
                             reply_markup=comp_pair_btn)        
    else:
        await msg.answer(text="""❤️‍🔥 Ты уже сделала максимум бесплатных разборов и проверок 💔
                         
Но ты можешь
                         
🔮 Открыть полный доступ - и задавать столько вопросов и  делать столько проверок совместимости, сколько нужно""",
                     reply_markup=energy_button)
        
        
@router.callback_query(F.data == "comp_yes")
async def ask_quest(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(text="1/3 На каком этапе ваши отношения?",
                     reply_markup=q1_markup)
    await state.set_state(CheckComp.quest1)
    
    
@router.callback_query(F.data == "comp_no")
async def send_quest(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(text="""💞 Напиши мне имена и даты рождения вашей пары — я проверю совместимость по Матрице Судьбы.

❗️ Всё в одном сообщении, в таком  формате:
Анна 14.02.2001
Дмитрий 24.07.2001""")
        
    await state.set_state(CheckComp.ask_names_dates)
                

@router.message(CheckComp.ask_names_dates)
async def ask_quest(msg: Message, state: FSMContext):
    pair_info = msg.text
    await state.update_data(pair_info = pair_info)
    await state.set_state(None)
    await msg.answer(text="1/3 На каком этапе ваши отношения?",
                     reply_markup=q1_markup)
    await state.set_state(CheckComp.quest1)
    
    
@router.message(CheckComp.quest1)
async def ask_quest(msg: Message, state: FSMContext):
    ans1 = msg.text
    await state.update_data(ans1 = ans1)
    await state.set_state(None)
    await msg.answer(text="2/3 Что тебя больше всего интересует?",
                     reply_markup=q2_markup)
    await state.set_state(CheckComp.quest2)
    

@router.message(CheckComp.quest2)
async def ask_quest(msg: Message, state: FSMContext):
    ans2 = msg.text
    await state.update_data(ans2 = ans2)
    await state.set_state(None)
    await msg.answer(text="3/3 Что ты хочешь от этих отношений?",
                     reply_markup=q3_markup)
    await state.set_state(CheckComp.quest3)
    
    
@router.message(CheckComp.quest3)
async def ask_quest(msg: Message, state: FSMContext, bot: Bot):
    ans3 = msg.text
    data = await state.get_data()
    ans1 = data.get('ans1')
    ans2 = data.get('ans2')
    pair_info = data.get('pair_info')
    
    try:   
        await state.set_state(None)
        await msg.answer(text="🔮 Делаю запрос во Вселенную...")
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
        await msg.answer(text="Выбери, что хочешь сделать дальше",
                         reply_markup=continue_markup)
        await state.set_state(None)
    
    except Exception as e:
        print(e)
        await msg.answer("Кажется, неполадки с космосом, подождем, когда пройдет ретроградный Меркурий")
        await state.clear()
    