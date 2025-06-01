from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.user import check_active_subscription, check_has_energy
from bot.keyboards.ask_keyboards import offer, ask_prompt, ask, continue_markup, ask_pair_btn
from bot.keyboards.main_keyboards import energy_button

from openai import AsyncOpenAI
from config import GPT_TOKEN


router = Router()
client = AsyncOpenAI(api_key=GPT_TOKEN)

class Ask(StatesGroup):
    ask_names_dates = State()
    ask_from_user = State()
    firs_ans = State()
    second_ans = State()

    

@router.message((F.text == "🔮Задать вопрос по отношениям🔮")
    | (F.text == "💌 Еще один вопрос про эти отношения"))
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id) or await check_has_energy(session, msg.from_user.id):
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
        await msg.answer(text="""❤️‍🔥 Ты уже сделала максимум бесплатных разборов и проверок 💔
                         
Но ты можешь
                         
🔮 Открыть полный доступ - и задавать столько вопросов и  делать столько проверок совместимости, сколько нужно""",
                     reply_markup=energy_button)
        

@router.message(F.text == "❓ Задать вопрос про отношения")     # вопрос из проверик на совместимость
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id) or await check_has_energy(session, msg.from_user.id):
        data = await state.get_data()
        
        if 'pair_info' in data:
            pair_info = data['pair_info']
            await msg.answer(text=f"Готовим ответ по этой паре?\n\n{pair_info}",
                             reply_markup=ask_pair_btn)
            await state.set_state(Ask.ask_from_user)
        else:
            await msg.answer(text="""Введи данные по вашей паре 👩‍❤️‍👨

❗️ Всё в одном сообщении, в формате:
Анна 14.02.2001
Дмитрий 24.07.2001""")
            await state.set_state(Ask.ask_names_dates)          
    else:
        await msg.answer(text="""❤️‍🔥 Ты уже сделала максимум бесплатных разборов и проверок 💔
                         
Но ты можешь
                         
🔮 Открыть полный доступ - и задавать столько вопросов и  делать столько проверок совместимости, сколько нужно""",
                     reply_markup=energy_button)
        
        
@router.callback_query(F.data == 'ask_yes')
async def send_quest(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
        
    if 'pair_info' in data:
        pair_info = data['pair_info']
        await callback.message.answer(text=offer)
        await state.set_state(Ask.ask_from_user)
         

@router.callback_query(F.data == 'ask_no')
async def send_quest(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(text="""Введи данные по вашей паре 👩‍❤️‍👨

❗️ Всё в одном сообщении, в формате:
Анна 14.02.2001
Дмитрий 24.07.2001""")
    await state.set_state(Ask.ask_names_dates) 


@router.message(F.text == "❓ Вопрос про другие отношения")
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    if await check_active_subscription(session, msg.from_user.id) or check_has_energy(session, msg.from_user.id):
        await state.clear()        
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
    await state.set_state(None)
    await msg.answer(text="Думаю 🧠")
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
    await msg.answer(text="Выбери что хочешь сделать дальше",
                     reply_markup=continue_markup)
    await state.set_state(None)
