import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# 🔑 Вставте сюди свій токен від BotFather
BOT_TOKEN = "8949974589:AAEF_mtYAqsgHhOTFFswyLET2FkDycSGG88"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ГОЛОВНЕ МЕНЮ (Reply Keyboard) ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋 Подати скаргу/звернення"),
            KeyboardButton(text="📢 Дайджест процедур на етапі громслухань"),
        ],
        [
            KeyboardButton(text="📞 Довідник інстанцій"),
            KeyboardButton(text="📚 База знань та алгоритми"),
        ],
        [
            KeyboardButton(text="🎓 Школа зеленої демократії"),
            KeyboardButton(text="ℹ️ Контакти ГС «ДТКР»"),
        ],
    ],
    resize_keyboard=True,
    persistent=True,
)


# --- ОБРОБКА КОМАНДИ /start ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    welcome_text = (
        "🌿 **Вітаємо у Telegram-сервісі «ЕкоСкарга ДТКР»!**\n\n"
        "Цей цифровий інструмент створений командою **ГС «Досить труїти Кривий Ріг»** за підтримки ПРООН "
        "у межах проєкту «Зелена демократія та громадський контроль».\n\n"
        "**За допомогою бота ви можете:**\n"
        "📋 Отримати шаблони скарг та звернень\n"
        "📢 Моніторити актуальні дозвільні процедури на етапі громадських слухань\n"
        "📞 Знайти контакти екологічних інстанцій\n"
        "📚 Ознайомитися з алгоритмами захисту довкіллєвих прав\n"
        "🎓 Долучитися до Школи зеленої демократії\n\n"
        "🔻 **Оберіть потрібний розділ у меню нижче:**"
    )
    await message.answer(
        welcome_text, reply_markup=main_keyboard, parse_mode="Markdown"
    )


# --- 1. КОНСТРУКТОР ЗВЕРНЕНЬ ---
@dp.message(F.text == "📋 Подати скаргу / звернення")
async def appeals_handler(message: types.Message):
    text = (
        "📋 **Конструктор звернень та скарг**\n\n"
        "Оберіть категорію порушення, щоб отримати готовий шаблон документа (.docx) "
        "та інструкцію щодо заповнення та відправки:"
    )
    # Інлайн-кнопки для вибору шаблонів
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💨 Забруднення повітря / пил",
                    callback_data="template_air",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Несанкціоноване сміттєзвалище",
                    callback_data="template_waste",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌳 Вирубка зелених насаджень",
                    callback_data="template_trees",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💧 Забруднення водойм / скиди",
                    callback_data="template_water",
                )
            ],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


# --- 2. ДАЙДЖЕСТ ПРОЦЕДУР НА ЕТАПІ ГРОМСЛУХАНЬ ---
@dp.message(F.text == "📢 Дайджест процедур на етапі громслухань")
async def digest_handler(message: types.Message):
    text = (
        "📢 **Дайджест процедур на етапі громслухань**\n\n"
        "Тут публікуються актуальні екологічні дозвільні процедури Криворізького регіону з Реєстрів ОВД, СЕО та ін."
        "та дедлайни для подання зауважень громадськості.\n\n"
        "📌 *Розділ оновлюється щотижня.*"
    )
    await message.answer(text, parse_mode="Markdown")


# --- 3. ДОВІДНИК ІНСТАНЦІЙ ---
@dp.message(F.text == "📞 Довідник інстанцій")
async def contacts_directory_handler(message: types.Message):
    text = (
        "📞 **Довідник контролюючих органів та гарячих ліній:**\n\n"
        "🔹 **Державна екологічна інспекція Південно-Західного округу**\n"
        "• Гаряча лінія: +38 (048) 705-40-00\n"
        "• Email: pzo@dei.gov.ua\n\n"
        "🔹 **Виконавчий комітет Криворізької міської ради**\n"
        "• Телефон: 1520 (управління екології)\n"
        "• Email: radakr@kr.gov.ua\n\n"
        "🔹 **Держпродспоживслужба у Дніпропетровській обл.**\n"
        "• Телефон: +38 (099) 723-16-99"
    )
    await message.answer(text, parse_mode="Markdown")


# --- 4. БАЗА ЗНАНЬ ---
@dp.message(F.text == "📚 База знань та алгоритми")
async def knowledge_base_handler(message: types.Message):
    text = (
        "📚 **База знань та алгоритми дій**\n\n"
        "• **Право на безпечне довкілля:** ст. 50 Конституції України.\n"
        "• **Build Back Better:** Принципи екологічної та сталої відбудови промислових регіонів.\n"
        "• **Розділ 27 EU Acquis:** Вимоги ЄС у сфері охорони довкілля та зміни клімату."
    )
    await message.answer(text, parse_mode="Markdown")


# --- 5. ШКОЛА ЗЕЛЕНОЇ ДЕМОКРАТІЇ ---
@dp.message(F.text == "🎓 Школа зеленої демократії")
async def school_handler(message: types.Message):
    text = (
        "🎓 **Школа зеленої демократії**\n\n"
        "Освітня програма від ГС «ДТКР» для активних містян, лідерів ОСББ та молоді. "
        "Дізнайтеся, як ефективно впливати на довкіллєві рішення у своїй громаді!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Перейти на сторінку Школи",
                    url="https://dtkr.com.ua",
                )
            ]
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


# --- 6. КОНТАКТИ ДТКР ---
@dp.message(F.text == "ℹ️ Контакти ГС «ДТКР»")
async def dtkr_info_handler(message: types.Message):
    text = (
        "ℹ️ **Громадська спілка «Досить труїти Кривий Ріг» (ДТКР)**\n\n"
        "Працюємо задля чистого довкілля та безпечного майбутнього Криворіжжя.\n\n"
        "🌐 **Сайт:** [dtkr.com.ua](https://dtkr.com.ua)\n"
        "✉️ **Email:** ecodtkr@gmail.com\n"
        "📞 **Телефон:** +38 (096) 091-69-55\n"
        "📲 **Facebook:** facebook.com/dosytKR/ "
    )
    await message.answer(
        text, parse_mode="Markdown", disable_web_page_preview=True
    )


# --- Обробка натискання на шаблони скарг ---
@dp.callback_query(F.data == "template_air")
async def template_air_cb(call: types.CallbackQuery):
    text = (
        "💨 **Скарга на забруднення повітря / пил**\n\n"
        "📄 [📥 Завантажити шаблон (.docx)](https://example.com/template-air)\n\n"
        "✏️ **Інструкція:**\n"
        "1. Заповніть ваші ПІБ, адресу та телефон у шапці.\n"
        "2. Вкажіть точний час, дату та локацію спостереження пилу/викидів.\n"
        "3. Надішліть підписану заяву на email ДЕІ (`pzo@dei.gov.ua`)."
    )
    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
