from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


main_reply_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,      # клавиатура скроется после первого использования
    keyboard=[        
        [
            KeyboardButton(text="🔮Задать вопрос по отношениям🔮")
        ],
        [
            KeyboardButton(text="💞Проверить совместимость💞")
        ],
        [
            KeyboardButton(text="🔮 Безграничный доступ")
        ]
    ]
)

energy_button = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🔮 Получить доступ", url='https://t.me/payment_matrix_bot')
    ]
])