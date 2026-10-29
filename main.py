import asyncio
import csv
import io
import logging
import os
import aiohttp
from aiohttp import web  
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# 🔑 Ваш токен від BotFather
BOT_TOKEN = "8949974589:AAEF_mtYAqsgHhOTFFswyLET2FkDycSGG88"

# 👑 Ваш Telegram ID для адмін-команд (щоб дізнатися свій ID, напишіть боту @userinfobot)
ADMIN_ID = 1218438551

# Просте збереження користувачів у пам'яті (у множину)
users_db = set()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# --- 1. ФІКТИВНИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER (ЩОБ БОТ НЕ ВИМИКАВСЯ) ---
async def handle_healthcheck(request):
    return web.Response(
        text="EcoScarha DTKR Bot is running 24/7!", status=200
    )


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))  # Render передає порт автоматично
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# --- 2. ГОЛОВНЕ МЕНЮ ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋 Подати скаргу / звернення"),
            KeyboardButton(text="📢 Дайджест ОВД та СЕО"),
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


# --- 3. ОБРОБКА КОМАНДИ /start ТА ЗБЕРЕЖЕННЯ КОРИСТУВАЧІВ ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    users_db.add(message.from_user.id)

    welcome_text = (
        "🌿 **Вітаємо у Telegram-сервісі «ЕкоСкарга ДТКР»!**\n\n"
        "Цей цифровий інструмент створений **ГС «Досить труїти Кривий Ріг»** за підтримки ПРООН "
        "у межах проєкту «Зелена демократія та громадський контроль».\n\n"
        "**За допомогою бота ви можете:**\n"
        "📋 Отримати шаблони скарг та звернень\n"
        "📢 Моніторити актуальні справи ОВД та СЕО\n"
        "📞 Знайти контакти екологічних інстанцій\n"
        "📚 Ознайомитися з алгоритмами захисту довкіллєвих прав\n"
        "🎓 Долучитися до Школи зеленої демократії\n\n"
        "🔻 **Оберіть потрібний розділ у меню нижче:**"
    )
    await message.answer(
        welcome_text, reply_markup=main_keyboard, parse_mode="Markdown"
    )


# --- 4. АДМІН-КОМАНДА /stats ДЛЯ ПЕРЕГЛЯДУ ПІДПИСНИКІВ ---
@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    # Дозволяємо перегляд лише адміну або показуємо для всіх за бажанням
    count = len(users_db)
    await message.answer(
        f"📊 **Статистика бота:**\n\n"
        f"👥 Загальна кількість користувачів, що запускали бота: **{count}**",
        parse_mode="Markdown",
    )


# --- 5. ОБРОБКА КНОПОК МЕНЮ ---
@dp.message(F.text == "📋 Подати скаргу / звернення")
async def appeals_handler(message: types.Message):
    users_db.add(message.from_user.id)
    text = (
        "📋 **Конструктор звернень та скарг**\n\n"
        "Оберіть категорію порушення, щоб отримати готовий шаблон документа (.docx) "
        "та інструкцію щодо заповнення:"
    )
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


import csv
import io

# 🔗 Вставте сюди скопійоване CSV-посилання з пунктів вище
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQX4VVekM7ZCLhwk1HRuUXPVCK0L5uQgmulQd60j3skRWuZe43cICCCJy-nw8uRREW4X-IecsWZ2APN/pub?gid=0&single=true&output=csv"


@dp.message(F.text == "📢 Дайджест ОВД та СЕО")
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

        text_lines = ["📢 **Дайджест процедур ОВД та СЕО**\n"]
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

            if not company and not case_num:
                continue

            has_cases = True
            header = f"🔹 **[{tp}] {company}**"
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

            text_lines.append("")

        if not has_cases:
            await msg.edit_text(
                "📢 **Дайджест ОВД та СЕО**\n\nНаразі немає активних справ у реєстрі."
            )
            return

        text_lines.append(
            "📌 *Для завантаження шаблонів зауважень скористайтеся розділом «📋 Подати скаргу / звернення».*"
        )
        final_text = "\n".join(text_lines)

        # Спочатку пробуємо відправити з форматуванням Markdown
        try:
            await msg.edit_text(
                final_text, parse_mode="Markdown", disable_web_page_preview=True
            )
        except Exception:
            # Якщо у тексті були спеціальні символи, відправляємо як звичайний текст
            await msg.edit_text(final_text, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Помилка дайджесту: {e}")
        await msg.edit_text(
            "⚠️ Виникла помилка під час оновлення дайджесту. Перевірте посилання на CSV у коді."
        )


@dp.message(F.text == "📞 Довідник інстанцій")
async def contacts_directory_handler(message: types.Message):
    users_db.add(message.from_user.id)
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


@dp.message(F.text == "📚 База знань та алгоритми")
async def knowledge_base_handler(message: types.Message):
    users_db.add(message.from_user.id)
    text = (
        "📚 **База знань та алгоритми дій**\n\n"
        "• **Право на безпечне довкілля:** ст. 50 Конституції України.\n"
        "• **Build Back Better:** Принципи екологічної та сталої відбудови промислових регіонів.\n"
        "• **Розділ 27 EU Acquis:** Вимоги ЄС у сфері охорони довкілля та зміни клімату."
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message(F.text == "🎓 Школа зеленої демократії")
async def school_handler(message: types.Message):
    users_db.add(message.from_user.id)
    text = (
        "🎓 **Школа зеленої демократії**\n\n"
        "Освітня програма від ГС «ДТКР» для активних містян, лідерів ОСББ та молоді."
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


@dp.message(F.text == "ℹ️ Контакти ГС «ДТКР»")
async def dtkr_info_handler(message: types.Message):
    users_db.add(message.from_user.id)
    text = (
        "ℹ️ **Громадська спілка «Досить труїти Кривий Ріг» (ДТКР)**\n\n"
        "Працюємо задля чистого довкілля та безпечного майбутнього Криворіжжя.\n\n"
        "🌐 **Сайт:** [dtkr.com.ua](https://dtkr.com.ua)\n"
        "✉️ **Email:** ecodtkr@gmail.com\n"
        "📲 **Facebook:** facebook.com/dosytKR \n"
    )
    await message.answer(
        text, parse_mode="Markdown", disable_web_page_preview=True
    )


# --- 6. ЗАПУСК БОТА ТА ВЕБ-СЕРВЕРА ОДНОЧАСНО ---
async def main():
    await start_web_server()  # Відкриває порт для Render
    await dp.start_polling(bot)  # Запускає Telegram-бота


if __name__ == "__main__":
    asyncio.run(main())
