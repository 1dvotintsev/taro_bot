from aiogram import F, Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.user import register_user, check_active_subscription, check_has_energy
from bot.keyboards.ask_keyboards import offer, ask_prompt, ask
import tempfile
import os
import asyncio
import openai
import io
from openai import AsyncOpenAI
from config import GPT_TOKEN


router = Router()
client = AsyncOpenAI(api_key=GPT_TOKEN)

class Ask(StatesGroup):
    ask_names_dates = State()
    ask_from_user = State()
    firs_ans = State()
    second_ans = State()

    

@router.message(F.text == "🔮Задать вопрос по отношениям🔮" or F.text == "❓ Задать вопрос про отношения")
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id):
        data = await state.get_data()
        
        if 'pair_info' in data:
            pair_info = data['pair_info']
            await msg.answer(text=offer)
            await state.set_state(Ask.ask_from_user)
        else:
            await msg.answer(text="""Введи данные по вашей паре 👩‍❤️‍👨

❗️ Всё в одном сообщении, в формате:
Анна 14.02.2001
Дмитрий 24.07.2001""")
            await state.set_state(Ask.ask_names_dates)          
    else:
        await msg.answer(text="Нет подписки")
        
        
@router.message(Ask.ask_names_dates)
async def ask_quest(msg: Message, state: FSMContext):
    pair_info = msg.text
    await state.update_data(pair_info = pair_info)
    await msg.answer(text=offer)
    await state.set_state(Ask.ask_from_user)


@router.message(Ask.ask_from_user)
async def ask_pending(
    msg: Message,
    state: FSMContext,
    bot: Bot,                       
):
    # 1. Получаем текст от пользователя
    if msg.voice:
        audio_buf = await bot.download(msg.voice)
        audio_buf.name = "voice.ogg" 

        tr = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buf,
            response_format="text",
            language="ru",
        )
        user_text = tr.strip()
    else:
        user_text = msg.text or ""
        
    await state.update_data(user_text = user_text)

    # 2. Отправляем текст в ChatGPT
    data = await state.get_data()
    chat = await client.chat.completions.create(
        model="gpt-4.1-2025-04-14", 
        messages=[
            {"role": "system", "content": ask_prompt},
            {"role": "user",
             "content": f"Вопрос: {user_text}\nИнформация о паре: {data['pair_info']}"}
        ],
        temperature=0.7,
        max_tokens=1000,
    )
    answer = chat.choices[0].message.content.strip()

    # 3. Сохраняем и отвечаем
    await state.update_data(first_ask=answer)
    await msg.answer(answer, reply_markup=ask)
    await state.set_state(Ask.firs_ans)
    
    
@router.message(Ask.firs_ans)
async def ask_pending(msg: Message, state: FSMContext, bot: Bot,):
    ans1 = msg.text
    await state.update_data(ans1 = ans1)
    data = await state.get_data()
    chat = await client.chat.completions.create(
        model="gpt-4.1-2025-04-14", 
        messages=[
            {"role": "system", "content": ask_prompt},
            {"role": "user",
             "content": f"Вопрос: {data['user_text']}\nИнформация о паре: {data['pair_info']}"},
            {"role": "assistant", "content":data['first_ask']},
            {"role": "user", "content":ans1}
            
        ],
        temperature=0.7,
        max_tokens=1000,
    )
    answer = chat.choices[0].message.content.strip() 
    await state.update_data(second_ask = answer)
    await msg.answer(answer, reply_markup=ask)
    await state.set_state(Ask.second_ans)
    
    
@router.message(Ask.second_ans)
async def ask_pending(msg: Message, state: FSMContext, bot: Bot,):
    ans2 = msg.text
    await state.update_data(ans2 = ans2)
    data = await state.get_data()
    chat = await client.chat.completions.create(
        model="gpt-4.1-2025-04-14", 
        messages=[
            {"role": "system", "content": ask_prompt},
            {"role": "user",
             "content": f"Вопрос: {data['user_text']}\nИнформация о паре: {data['pair_info']}"},
            {"role": "assistant", "content":data['first_ask']},
            {"role": "user", "content":data['ans1']},
            {"role": "assistant", "content":data['second_ask']},
            {"role": "user", "content":ans2},
            
        ],
        temperature=0.7,
        max_tokens=1000,
    )
    answer = chat.choices[0].message.content.strip() 
    await state.update_data(res = answer)
    await msg.answer(answer)
    await state.set_state(None)
