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
            KeyboardButton(text="Как работает бот")
        ]
    ]
)