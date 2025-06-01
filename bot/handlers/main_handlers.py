from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_keyboards import main_reply_kb, energy_button

from database.user import register_user, check_active_subscription


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
                         """Хочешь узнать, есть ли в ваше паре совместимость?
                         
За 3 минуты я помогу:
                         
💕 Проверить совместимость по Матрице Судьбы
🌱 Узнать, есть ли потенциал у отношений
⚡️ Какие конфликты могут всплыть - и как их сгладить
                         
Проверь, что заложено в ваших Матрицах Судьбы""",
                        reply_markup=main_reply_kb)
    else:
        await msg.answer(text = 
                         """Хочешь узнать, есть ли в ваше паре совместимость?
                         
За 3 минуты я помогу:
                         
💕 Проверить совместимость по Матрице Судьбы
🌱 Узнать, есть ли потенциал у отношений
⚡️ Какие конфликты могут всплыть - и как их сгладить
                         
Проверь, что заложено в ваших Матрицах Судьбы""",
                        reply_markup=main_reply_kb)


@router.message(F.text == "🔮 Безграничный доступ")
async def send_quest(msg: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    if not await check_active_subscription(session, msg.from_user.id):
        await msg.answer(text="""❤️‍🔥 Я могу всегда быть с тобой на связи и проконсультировать в любой ситуцации 💔
                         
Ты можешь
                         
🔮 Открыть полный доступ - и задавать столько вопросов и  делать столько проверок совместимости, сколько нужно""",
                     reply_markup=energy_button)
    else:
        await msg.answer(text="""❤️‍🔥 Я всегда с тобой на связи ❤️‍🔥
                         
🔮 Ты можешь задавать столько вопросов и  делать столько проверок совместимости, сколько нужно""")