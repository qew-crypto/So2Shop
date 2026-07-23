import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

from config_loader import BOT_TOKEN, ADMIN_IDS
from database import DB
from handlers.user_handlers import (
    cmd_start, cmd_profile, cmd_history, cmd_help, cmd_support, cmd_info,
    callback_tier_select, callback_buy, send_profile
)
from handlers.payment_handlers import callback_pay_method, callback_pay_amount, callback_bonus_claim
from handlers.activate_handlers import (
    callback_nav_activate, process_activate, callback_dl_start,
    callback_dl_file, callback_dl_qr
)
from handlers.admin_handlers import (
    cmd_admin, adm_stats, adm_users, adm_user_action, adm_add_bal, adm_grant_tier,
    adm_keys, adm_keygen, adm_tx, adm_bc_start, adm_bc_audience, adm_home
)
from middlewares.keyboards import main_menu_kb, catalog_kb, topup_method_kb, topup_amount_kb

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger("standoff-bot")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ======= ДИСПАТЧЕРЫ =======
async def back_home(bot, cq):
    await cq.message.edit_text(
        "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыбери действие:",
        parse_mode=ParseMode.HTML
    )
    await cq.message.answer("👇 Используй кнопки ниже:", reply_markup=main_menu_kb())
    try: await cq.answer()
    except: pass

async def nav_catalog(bot, cq):
    text = (
        "💎 <b>ТАРИФЫ И ЦЕНЫ</b>\n\n"
        "🎮 Выбери свой уровень и получи мгновенный доступ к читам!"
    )
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=catalog_kb())
    await cq.answer()

async def nav_topup(bot, cq):
    text = (
        "💳 <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        "💵 Все способы оплаты:\n"
        "• 📱 СБП — по номеру (без комиссии)\n"
        "• 💳 Карта — МИР/Visa/MC\n"
        "• ₿ Крипта — USDT TRC-20\n\n"
        "🎁 Акция: пополни от 1000 ₽ — бонус +10%\n\n"
        f"⚠️ <b>DEMO-режим</b> — деньги не списываются"
    )
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=topup_method_kb())
    await cq.answer()

async def nav_profile(bot, cq):
    user = DB.get_user(cq.from_user.id) or DB.create_user(cq.from_user.id, cq.from_user.first_name or 'P')
    from handlers.user_handlers import send_profile
    await cq.message.delete()
    await send_profile(bot, cq.message.chat.id, user)
    await cq.answer()

async def callback_back_handlers(bot: Bot, cq: types.CallbackQuery):
    action = cq.data.split(':')[1] if cq.data.count(':')>=2 else cq.data
    if action == 'home': await back_home(bot, cq)
    elif action == 'profile': await nav_profile(bot, cq)

async def callback_nav_handlers(bot: Bot, cq: types.CallbackQuery):
    target = cq.data.split(':')[1]
    if target == 'catalog': await nav_catalog(bot, cq)
    elif target == 'topup': await nav_topup(bot, cq)
    elif target == 'profile': await nav_profile(bot, cq)
    elif target == 'activate': await callback_nav_activate(bot, cq)

# ===== Реплай-кнопки (основное меню) =====
async def reply_catalog(bot: Bot, message: types.Message):
    text = "💎 <b>ТАРИФЫ И ЦЕНЫ</b>\n\n🎮 Выбери свой уровень!"
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=catalog_kb())

async def reply_profile(bot: Bot, message: types.Message):
    user = DB.get_user(message.from_user.id) or DB.create_user(message.from_user.id, message.from_user.first_name or 'P')
    await send_profile(bot, message.chat.id, user)

async def reply_activate(bot: Bot, message: types.Message):
    await message.answer("🎫 Введи ключ <code>XXXX-XXXX-XXXX-XXXX</code>:", parse_mode=ParseMode.HTML)

async def reply_topup(bot: Bot, message: types.Message):
    text = (
        "💳 <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        "💵 Выбери способ:"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=topup_method_kb())

async def reply_info(bot: Bot, message: types.Message):
    await cmd_info(bot, message)

async def reply_support(bot: Bot, message: types.Message):
    await cmd_support(bot, message)

# ===== Обработка сообщений от юзеров (для админ-операций и активации) =====
async def process_user_message(bot: Bot, message: types.Message):
    if not message.text: return
    text = message.text.strip()

    # Активация ключа
    if len(text) >= 16 and any(c.isalnum() for c in text):
        await process_activate(bot, message)
        return

    # Админ: начисление баланса
    if message.from_user.id in ADMIN_IDS and hasattr(bot, '_adm_state') and bot._adm_state:
        state, uid = bot._adm_state
        if state == 'addbal':
            try:
                amount = float(text.replace(',','.').replace(' ',''))
                user_data = DB.get_all_users().get(str(uid))
                if user_data:
                    from database import User
                    user = User(uid, user_data)
                    user.balance += amount
                    DB.save_user(user)
                    DB.add_transaction(uid, 'admin_add', amount, 'admin', f"Админ начислил {amount}₽")
                    DB.add_to_user_history(uid, {'type':'bonus','method':'Админ-начисление','amount':amount,'sign':'+' if amount>0 else '-','date':datetime.now().strftime('%d.%m.%Y %H:%M')})
                    await message.answer(f"✅ Начислено <b>{amount:+.2f} ₽</b> юзеру <code>{uid}</code>\n💰 Новый баланс: {user.balance:.2f}₽", parse_mode=ParseMode.HTML)
                    try: await bot.send_message(uid, f"💳 <b>АДМИН-НАЧИСЛЕНИЕ</b>\n\nЗачислено: <b>{amount:+.2f} ₽</b>\n💰 Новый баланс: <b>{user.balance:.2f} ₽</b>", parse_mode=ParseMode.HTML)
                    except: pass
                bot._adm_state = None
            except ValueError:
                await message.answer("❌ Неверная сумма. Введи число.")
            return

    # Админ: рассылка
    if message.from_user.id in ADMIN_IDS and hasattr(bot, '_bc_state') and bot._bc_state:
        audience = bot._bc_audience
        users = list(DB.get_all_users().values())
        sent = 0; fails = 0
        await message.answer(f"📢 Начинаю рассылку в группу <b>{audience}</b>...")
        for u in users:
            uid = u['uid']
            if audience == 'active' and not u.get('tier'): continue
            if audience == 'top' and u.get('tier') not in ('VIP','PREMIUM'): continue
            try:
                await bot.send_message(uid, text, parse_mode=ParseMode.HTML)
                sent += 1
                await asyncio.sleep(0.05)
            except: fails += 1
        await message.answer(f"✅ Рассылка завершена!\n📨 Отправлено: <b>{sent}</b>\n❌ Не доставлено: <b>{fails}</b>", parse_mode=ParseMode.HTML)
        bot._bc_state = False
        return

# ====== Регистрация ======
def register_handlers(dp: Dispatcher):
    # Команды
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_profile, Command("profile"))
    dp.message.register(cmd_history, Command("history"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_support, Command("support"))
    dp.message.register(cmd_info, Command("info"))
    dp.message.register(cmd_admin, Command("admin"))
    dp.message.register(cmd_activate, Command("activate"))

    # Реплай-кнопки
    dp.message.register(reply_catalog, F.text == "💎 Купить подписку")
    dp.message.register(reply_profile, F.text == "👤 Мой профиль")
    dp.message.register(reply_activate, F.text == "🎫 Активировать ключ")
    dp.message.register(reply_topup, F.text == "💳 Пополнить баланс")
    dp.message.register(reply_info, F.text == "ℹ️ О сервисе")
    dp.message.register(reply_support, F.text == "📞 Поддержка")

    # Generic message for activation code / admin input
    dp.message.register(process_user_message)

    # Коллбэки
    dp.callback_query.register(callback_tier_select, F.data.startswith("tier:"))
    dp.callback_query.register(callback_buy, F.data.startswith("buy:"))
    dp.callback_query.register(callback_pay_method, F.data.startswith("pay:"))
    dp.callback_query.register(callback_pay_amount, F.data.startswith("amt:"))
    dp.callback_query.register(callback_bonus_claim, F.data == "bonus:claim")
    dp.callback_query.register(callback_nav_activate, F.data == "nav:activate")
    dp.callback_query.register(callback_dl_start, F.data == "dl:start")
    dp.callback_query.register(callback_dl_file, F.data == "dl:file")
    dp.callback_query.register(callback_dl_qr, F.data == "dl:qr")
    dp.callback_query.register(callback_back_handlers, F.data.startswith("back:"))
    dp.callback_query.register(callback_nav_handlers, F.data.startswith("nav:"))
    # noop для пагинации
    dp.callback_query.register(lambda b,c: c.answer(), F.data == "noop")

    # Админские
    dp.callback_query.register(adm_home, F.data == "adm:home")
    dp.callback_query.register(adm_stats, F.data == "adm:stats")
    dp.callback_query.register(adm_users, F.data.startswith("adm:users:"))
    dp.callback_query.register(adm_user_action, F.data.startswith("adm:uadd:"))
    dp.callback_query.register(adm_user_action, F.data.startswith("adm:ugrant:"))
    dp.callback_query.register(adm_user_action, F.data.startswith("adm:uban:"))
    dp.callback_query.register(adm_user_action, F.data.startswith("adm:uwarn:"))
    dp.callback_query.register(adm_grant_tier, F.data.startswith("adm:grantt:"))
    dp.callback_query.register(adm_add_bal, F.data.startswith("adm:uaddbal:"))
    dp.callback_query.register(adm_keys, F.data.startswith("adm:keys:"))
    dp.callback_query.register(adm_keygen, F.data.startswith("adm:keygen:"))
    dp.callback_query.register(adm_tx, F.data.startswith("adm:tx:"))
    dp.callback_query.register(adm_bc_start, F.data == "adm:broadcast")
    dp.callback_query.register(adm_bc_audience, F.data.startswith("adm:bc:"))

async def main():
    log.info("🤖 STAND FX Bot started")
    register_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
