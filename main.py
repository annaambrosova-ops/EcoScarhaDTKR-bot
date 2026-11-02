import asyncio
import csv
import io
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiohttp import web

# ==========================================
# 🔑 НАЛАШТУВАННЯ ТА НАЛАШТОВУВАНІ ЗМІННІ
# ==========================================

BOT_TOKEN = "8121175620:AAG-ВАШ_ТОКЕН_СЮДИ"  # Вкажіть ваш актуальний токен бота
ADMIN_ID = 123456789  # Вкажіть ваш Telegram ID

# 🔗 Ваше публічне CSV-посилання на Google Таблицю Дайджесту
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQX4VVekM7ZCLhwk1HRuUXPVCKOL5uQgmulQd60j3skRWuZe43cICCCJy-nw8uRREW4X-lecsWZ2APN/pub?gid=0&single=true&output=csv"

# 📌 Текст опису бота (використовується для /start та кнопки "ℹ️ Про бота")
ABOUT_TEXT = (
    "🤖 **Ласкаво просимо до бота «ЕкоСкарга ДТКР»!**\n\n"
    "Цей цифровий сервіс створено Громадською спілкою «Досить труїти Кривий Ріг» "
    "за підтримки ПРООН у межах проєкту «Зелена демократія та громадський контроль».\n\n"
    "**Чим корисний бот:**\n"
    "• 📋 **Подати скаргу / звернення:** покрокові алгоритми та завантаження готових шаблонів звернень (.docx).\n"
    "• 📢 **Дайджест дозвільних процедур:** щотижневий моніторинг ОВД/СЕО, дедлайнів та громадських слухань.\n"
    "• 📞 **Довідник інстанцій:** контакти та гарячі лінії контролюючих органів.\n"
    "• 📚 **База знань:** роз'яснення екологічних прав та норм законодавства.\n\n"
    "💡 Обирайте потрібний розділ у меню нижче, щоб розпочати роботу!"
)

# База користувачів у пам'яті
users_db = set()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==========================================
# ⌨️ КЛАВІАТУРИ Меню
# ==========================================

# 1. Головна клавіатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Подати скаргу / звернення")],
        [
            KeyboardButton(text="📢 Дайджест дозвільних процедур"),
            KeyboardButton(text="📞 Довідник інстанцій"),
        ],
        [
            KeyboardButton(text="📚 База знань"),
            KeyboardButton(text="🎓 Школа зеленої демократії"),
        ],
        [
            KeyboardButton(text="ℹ️ Контакти ГС «ДТКР»"),
            KeyboardButton(text="ℹ️ Про бота"),
        ],
    ],
    resize_keyboard=True,
)


# ==========================================
# 🌐 ВЕБ-СЕРВЕР ДЛЯ RENDER (Keep-Alive)
# ==========================================


async def handle_healthcheck(request):
    return web.Response(
        text="EcoScarha DTKR Bot is running 24/7!", status=200
    )


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# ==========================================
# 🤖 ОБРОБНИКИ КОМАНД ТА КНОПОК
# ==========================================


# /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    users_db.add(message.from_user.id)
    await message.answer(
        ABOUT_TEXT, reply_markup=main_keyboard, parse_mode="Markdown"
    )


# ℹ️ Про бота
@dp.message(F.text == "ℹ️ Про бота")
async def about_handler(message: types.Message):
    users_db.add(message.from_user.id)
    await message.answer(
        ABOUT_TEXT, reply_markup=main_keyboard, parse_mode="Markdown"
    )


# /stats (Адміністративна статистика)
@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"📊 **Статистика бота:**\n\nКількість унікальних користувачів: **{len(users_db)}**",
            parse_mode="Markdown",
        )
    else:
        await message.answer("⚠️ Ця команда доступна лише адміністратору.")


# 📢 Дайджест дозвільних процедур (Отримання CSV з Google Sheets)
@dp.message(F.text == "📢 Дайджест дозвільних процедур")
async def digest_handler(message: types.Message):
    users_db.add(message.from_user.id)
    msg = await message.answer("🔄 Завантажую актуальний дайджест...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GOOGLE_SHEET_CSV_URL) as response:
                if response.status != 200:
                    await msg.edit_text(
                        "⚠️ Не вдалося завантажити Google Таблицю (помилка доступу)."
                    )
                    return
                content = await response.text()

        f = io.StringIO(content)
        reader = csv.DictReader(f)

        text_lines = ["📢 **Дайджест дозвільних процедур (ОВД/СЕО)**\n"]
        has_cases = False

        for row in reader:
            tp = row.get("Тип дозвільної процедури", "").strip()
            company = row.get("Підприємство/Замовник", "").strip()
            case_num = row.get("Номер справи", "").strip()
            desc = row.get("Короткий опис діяльності", "").strip()
            stage = row.get("Стадія", "").strip()
            deadline = row.get("Дедлайн для подання зауважень", "").strip()
            hearings = row.get("Дата та час слухань", "").strip()
            link = row.get("Посилання на справу в Реєстрі", "").strip()
            hearings_link = row.get(
                "Посилання на громадські слухання", ""
            ).strip()

            if not company and not case_num:
                continue

            has_cases = True
            header = f"🔹 **{tp} {company}**"
            if case_num:
                header += f" (Справа №`{case_num}`)"

            text_lines.append(header)
            if desc:
                text_lines.append(f"• **Діяльність:** {desc}")
            if stage:
                text_lines.append(f"• **Стадія:** {stage}")
            if hearings:
                text_lines.append(f"• **Слухання:** {hearings}")
            if deadline:
                text_lines.append(f"• **Дедлайн зауважень:** {deadline}")
            if link and link.startswith("http"):
                text_lines.append(f"🌐 [Переглянути у Реєстрі]({link})")
            if hearings_link and hearings_link.startswith("http"):
                text_lines.append(
                    f"🎧 [Долучитися / Інфо про слухання]({hearings_link})"
                )

            text_lines.append("")

        if not has_cases:
            await msg.edit_text(
                "📢 **Дайджест дозвільних процедур**\n\nНаразі немає активних справ у реєстрі."
            )
            return

        text_lines.append(
            "📌 *Для завантаження шаблонів зауважень скористайтеся розділом «📋 Подати скаргу / звернення».*"
        )
        final_text = "\n".join(text_lines)

        try:
            await msg.edit_text(
                final_text, parse_mode="Markdown", disable_web_page_preview=True
            )
        except Exception:
            await msg.edit_text(final_text, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Помилка дайджесту: {e}")
        await msg.edit_text(
            "⚠️ Виникла помилка під час оновлення дайджесту. Перевірте посилання на CSV у коді."
        )


# ℹ️ Контакти ГС «ДТКР»
@dp.message(F.text == "ℹ️ Контакти ГС «ДТКР»")
async def contacts_handler(message: types.Message):
    users_db.add(message.from_user.id)

text = (
    " 🌿 **Громадська спілка «Досить труїти Кривий Ріг» (ГС ДТКР)**\n\n"
    "Ми об'єднуємо містян, експертів та активістів задля екологічної безпеки та сталого розвитку України.\n\n"
    "Обирайте зручний майданчик та стежте за нашими новинами, анонсами та екологічними моніторингами!"
)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Офіційний сайт", url="https://dtkr.com.ua"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    url="https://www.instagram.com/stop_poisoning_kryvyi_rih/",
                ),
                InlineKeyboardButton(
                    text="🎵 TikTok", url="https://www.tiktok.com/@stop_poisoning_kr?_t=ZM-90v9ja7KDf6&_r=1"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📘 Facebook",
                    url="https://www.facebook.com/dosytKR/",
                ),
                InlineKeyboardButton(
                    text="✈️ Telegram-канал", url="https://t.me/stoppoisonKR"
                ),
            ],
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# 📋 Подати скаргу / звернення (Заглушка для майбутніх кнопок)
@dp.message(F.text == "📋 Подати скаргу / звернення")
async def complaints_handler(message: types.Message):
    users_db.add(message.from_user.id)
    await message.answer(
        "📋 Розділ **«Подати скаргу / звернення»** наразі наповнюється матеріалами."
    )


# 📞 Довідник інстанцій (Заглушка для майбутніх кнопок)
@dp.message(F.text == "📞 Довідник інстанцій")
async def directory_handler(message: types.Message):
    users_db.add(message.from_user.id)
    await message.answer(
        "📞 Розділ **«Довідник інстанцій»** наразі наповнюється контактами."
    )


# 📚 База знань
@dp.message(F.text == "📚 База знань")
async def kb_handler(message: types.Message):
    users_db.add(message.from_user.id)
    await message.answer(
        "📚 Розділ **«База знань»** наразі наповнюється статтями."
    )


# 🎓 Школа зеленої демократії
@dp.message(F.text == "🎓 Школа зеленої демократії")
async def school_handler(message: types.Message):
    users_db.add(message.from_user.id)
    await message.answer(
        "🎓 Розділ **«Школа зеленої демократії»** готує анонси нових тренінгів."
    )


# ==========================================
# 🚀 ЗАПУСК СЕРВЕРУ ТА БОТА
# ==========================================


async def main():
    await start_web_server()  # Відкриває порт для Render
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
