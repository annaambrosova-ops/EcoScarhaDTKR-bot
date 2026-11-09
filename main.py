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

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8949974589:AAFD_gSHXF-1OrPbDFrWO7kMjuDXjf04ERc"
)
ADMIN_ID = 1218438551

# 🔗 Публічне CSV-посилання на Google Таблицю Дайджесту
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQX4VVekM7ZCLhwk1HRuUXPVCK0L5uQgmulQd60j3skRWuZe43cICCCJy-nw8uRREW4X-IecsWZ2APN/pub?gid=0&single=true&output=csv"

# 📝 Google Form URL для фонової фіксації метрик
FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfYWUz4EUQ5MaidbSJ5Ia68htaKmLuM0wgsC1untD5AWSrtmA/formResponse"
ENTRY_USER_ID = "entry.1958461916"
ENTRY_USER_NAME = "entry.419983157"
ENTRY_BUTTON_NAME = "entry.1993283542"

# 📌 Опис бота (для /start та кнопки "ℹ️ Про бота")
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

# База користувачів у оперативній пам'яті (для миттєвої розсилки)
users_db = set()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==========================================
# 📊 ФОНОВА РЕЄСТРАЦІЯ ТА МЕТРИКИ В GOOGLE FORM
# ==========================================


async def log_user_to_google_form(user: types.User, button_name: str = "/start"):
    """Фоново відправляє ID, username та назву натиснутої кнопки у Google Form."""
    users_db.add(user.id)

    user_name = user.username or f"{user.first_name} {user.last_name or ''}".strip()
    data = {
        ENTRY_USER_ID: str(user.id),
        ENTRY_USER_NAME: user_name,
        ENTRY_BUTTON_NAME: button_name,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(FORM_RESPONSE_URL, data=data) as resp:
                logging.info(f"Google Form HTTP Status: {resp.status}")
                if resp.status != 200:
                    body = await resp.text()
                    logging.error(f"Google Form Response Body: {body[:200]}")
    except Exception as e:
        logging.error(f"Помилка фонового запису в Google Form: {e}")


# ==========================================
# ⌨️ КЛАВІАТУРИ
# ==========================================

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
    asyncio.create_task(log_user_to_google_form(message.from_user, "/start"))
    await message.answer(
        ABOUT_TEXT, reply_markup=main_keyboard, parse_mode="Markdown"
    )


# ℹ️ Про бота
@dp.message(F.text == "ℹ️ Про бота")
async def about_handler(message: types.Message):
    asyncio.create_task(log_user_to_google_form(message.from_user, "ℹ️ Про бота"))
    await message.answer(
        ABOUT_TEXT, reply_markup=main_keyboard, parse_mode="Markdown"
    )


# 📊 /stats (Адміністративна статистика)
@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"📊 **Поточна статистика сесії:**\n\n"
            f"Активних користувачів у пам'яті: **{len(users_db)}**\n\n"
            f"💡 *Повну статистику унікальних користувачів та кліків по кнопках дивіться у вашій Google Таблиці (аркуш «Відповіді на форму 1»).*",
            parse_mode="Markdown",
        )
    else:
        await message.answer("⚠️ Ця команда доступна лише адміністратору.")


# 📢 /broadcast (Масова розсилка від адміна)
@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Ця команда доступна лише адміністратору.")
        return

    text_to_send = message.text.replace("/broadcast", "").strip()

    if not text_to_send:
        await message.answer(
            "⚠️ **Як користуватися розсилкою:**\n\n"
            "Введіть команду та через пробіл напишіть текст повідомлення.\n\n"
            "Приклад:\n`/broadcast Шановні підписники! Оновлено дайджест процедур ОВД.`",
            parse_mode="Markdown",
        )
        return

    if not users_db:
        await message.answer("⚠️ База активної сесії порожня.")
        return

    status_msg = await message.answer(
        f"🚀 Розпочинаю розсилку для {len(users_db)} користувачів..."
    )

    successful = 0
    failed = 0

    for user_id in list(users_db):
        try:
            await bot.send_message(
                user_id, text_to_send, disable_web_page_preview=True
            )
            successful += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Не вдалося надіслати {user_id}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ **Розсилку завершено!**\n\n"
        f"Успішно доставлено: **{successful}**\n"
        f"Не доставлено: **{failed}**",
        parse_mode="Markdown",
    )


# 📢 Дайджест дозвільних процедур
@dp.message(F.text == "📢 Дайджест дозвільних процедур")
async def digest_handler(message: types.Message):
    asyncio.create_task(
        log_user_to_google_form(
            message.from_user, "📢 Дайджест дозвільних процедур"
        )
    )
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

            # 🛡 СУВОРА ФІЛЬТРАЦІЯ ПОСИЛАНЬ (Блокуємо чужі t.me та рекламу)
            if link and link.startswith("http") and "t.me" not in link:
                text_lines.append(f"🌐 [Переглянути у Реєстрі]({link})")
            if (
                hearings_link
                and hearings_link.startswith("http")
                and "t.me" not in hearings_link
            ):
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
    asyncio.create_task(
        log_user_to_google_form(message.from_user, "ℹ️ Контакти ГС «ДТКР»")
    )

    text = (
        "🌿 **Громадська спілка «Досить труїти Кривий Ріг» (ГС ДТКР)**\n\n"
        "Ми об'єднуємо містян, експертів та активістів задля екологічної безпеки та сталого розвитку України.\n"
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
                    text="🎵 TikTok",
                    url="https://www.tiktok.com/@stop_poisoning_kr?_t=ZM-90v9ja7KDf6&_r=1",
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


# Заглушки для інших кнопок
@dp.message(F.text == "📋 Подати скаргу / звернення")
async def complaints_handler(message: types.Message):
    asyncio.create_task(
        log_user_to_google_form(
            message.from_user, "📋 Подати скаргу / звернення"
        )
    )
    await message.answer(
        "📋 Розділ **«Подати скаргу / звернення»** наразі наповнюється матеріалами."
    )


@dp.message(F.text == "📞 Довідник інстанцій")
async def directory_handler(message: types.Message):
    asyncio.create_task(
        log_user_to_google_form(message.from_user, "📞 Довідник інстанцій")
    )
    await message.answer(
        "📞 Розділ **«Довідник інстанцій»** наразі наповнюється контактами."
    )


@dp.message(F.text == "📚 База знань")
async def kb_handler(message: types.Message):
    asyncio.create_task(
        log_user_to_google_form(message.from_user, "📚 База знань")
    )
    await message.answer(
        "📚 Розділ **«База знань»** наразі наповнюється статтями."
    )


@dp.message(F.text == "🎓 Школа зеленої демократії")
async def school_handler(message: types.Message):
    asyncio.create_task(
        log_user_to_google_form(
            message.from_user, "🎓 Школа зеленої демократії"
        )
    )
    await message.answer(
        "🎓 Розділ **«Школа зеленої демократії»** готує анонси нових тренінгів."
    )


# ==========================================
# 🚀 ЗАПУСК СЕРВЕРУ ТА БОТА
# ==========================================


async def main():
    await start_web_server()
    # Скидає застряглі з'єднання та очищає накопичені оновлення для усунення TelegramConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
