import random, string, datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from database import DB, User
from config_loader import TIERS, TIER_RANK, ADMIN_IDS, SUPPORT, get_tier
from middlewares.keyboards import (
    main_menu_kb, catalog_kb, tier_buy_kb, topup_method_kb, topup_amount_kb,
    profile_kb, download_kb, admin_main_kb, admin_users_kb, admin_user_actions_kb,
    admin_keys_kb, admin_broadcast_kb
)

def make_key_code() -> str:
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    s = ''
    for i in range(16):
        if i>0 and i%4==0: s += '-'
        s += chars[random.randint(0, len(chars)-1)]
    return s

async def send_profile(bot: Bot, chat_id: int, user: User):
    tier = user.tier or 'НЕТ АКТИВНОЙ'
    keys_used = sum(1 for k in user.keys if k['status']=='active')
    keys_total = len(user.keys)
    text = (
        f"👤 <b>ТВОЙ ПРОФИЛЬ</b>\n\n"
        f"🆔 User ID: <code>{user.uid}</code>\n"
        f"👤 Ник: <b>{user.name}</b>\n"
        f"📅 Регистрация: {user.reg_date}\n\n"
        f"💎 <b>Тариф:</b> {tier}\n"
        f"💰 <b>Баланс:</b> {user.balance:.2f} ₽\n"
        f"🎫 <b>Ключей активировано:</b> {user.active_key and 'да' or 'нет'}\n"
        f"⏳ <b>Всего активаций:</b> {user.activations}\n"
        f"📥 <b>Скачиваний:</b> {user.downloads}\n\n"
        f"📊 История операций: /history"
    )
    kb = profile_kb(active_key=bool(user.active_key))
    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def cmd_start(bot: Bot, message: types.Message):
    uid = message.from_user.id
    user = DB.get_user(uid)
    if not user:
        user = DB.create_user(uid, message.from_user.first_name or 'Player', message.from_user.username or '')
        greeting = f"🎉 <b>Добро пожаловать в STAND FX!</b>\n\nПривет, <b>{user.name}</b>!\nМы дарим тебе <b>500 ₽ бонус</b> на первую покупку 🚀\n\n"
    else:
        greeting = f"👋 С возвращением, <b>{user.name}</b>!\n\n"
    text = (
        greeting +
        "🔥 <b>ПРИВАТНЫЕ ЧИТЫ STANDOFF 2</b>\n\n"
        "🛡️ Без банов | 📱 Android | ⚡ Запуск за 30 сек\n"
        "🎯 Aimbot • Wallhack • ESP • SkinChanger\n\n"
        "👇 Выбери действие:"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())

async def cmd_profile(bot: Bot, message: types.Message):
    user = DB.get_user(message.from_user.id) or DB.create_user(message.from_user.id, message.from_user.first_name or 'Player')
    await send_profile(bot, message.chat.id, user)

async def cmd_history(bot: Bot, message: types.Message):
    user = DB.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Профиль не найден. Нажми /start")
        return
    history = user.data.get('history', [])
    if not history:
        await message.answer("📜 История пуста")
        return
    text = "📜 <b>ИСТОРИЯ ОПЕРАЦИЙ</b>\n\n"
    for h in history[:15]:
        icon = {'+': '🟢', '-': '🔴', '•': '⚪'}.get(h.get('sign','•'), '⚪')
        text += f"{icon} {h.get('method','')} — {h.get('amount',0)} ₽\n   <i>{h.get('date','')}</i>\n"
    await message.answer(text, parse_mode=ParseMode.HTML)

async def cmd_help(bot: Bot, message: types.Message):
    text = (
        "ℹ️ <b>STAND FX — СПРАВКА</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start — Главное меню\n"
        "/profile — Мой профиль\n"
        "/history — История операций\n"
        "/activate — Активировать ключ\n"
        "/support — Связаться с поддержкой\n"
        "/info — О сервисе\n\n"
        f"💬 Поддержка: {SUPPORT}\n"
        f"📢 Канал: @standfx_channel"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

async def cmd_support(bot: Bot, message: types.Message):
    text = (
        "📞 <b>ПОДДЕРЖКА</b>\n\n"
        f"💬 Telegram: {SUPPORT}\n"
        "⏱ Среднее время ответа: ~5 мин\n"
        "🇷🇺 Русскоязычная поддержка 24/7\n\n"
        "<i>Прежде чем писать — посмотри /info и FAQ в боте.</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

async def cmd_info(bot: Bot, message: types.Message):
    text = (
        "ℹ️ <b>О СЕРВИСЕ</b>\n\n"
        "🏆 STAND FX — топовый приватный софт для Standoff 2\n"
        "🎮 Более 12 480 активаций\n"
        "📅 364 дня без единой волны банов\n\n"
        "<b>Что мы даём:</b>\n"
        "• 🎯 Aimbot с тонкими настройками\n"
        "• 👁️ ESP через стены\n"
        "• 🪄 Magic Bullet\n"
        "• 🎨 Бесплатные скины\n"
        "• 🛡️ Анти-бан система\n"
        "• 📱 Работает на Android 8+ без рута\n\n"
        "<b>Как это работает:</b>\n"
        "1️⃣ Пополни баланс в боте\n"
        "2️⃣ Купи тариф (BASE/VIP/PREMIUM)\n"
        "3️⃣ Получи ключ\n"
        "4️⃣ Скачай приложение\n"
        "5️⃣ Введи ключ и играй 🎮\n\n"
        "<i>Все платежи в DEMO-режиме.</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

# ====== BUY TIER ======
async def callback_tier_select(bot: Bot, cq: types.CallbackQuery):
    tier_id = cq.data.split(':')[1]
    tier = get_tier(tier_id)
    if not tier:
        await cq.answer("Тариф не найден")
        return
    features = '\n'.join([f"  ✅ {f}" for f in tier['features']])
    badge = "🔥 ХИТ ПРОДАЖ!\n" if tier.get('popular') else ""
    user = DB.get_user(cq.from_user.id)
    locked = user.tier and TIER_RANK[tier_id] < TIER_RANK[user.tier]
    warning = ""
    if user.tier == tier_id:
        warning = "\n\n⚠️ У тебя уже активирован этот тариф"
    elif locked:
        cur = get_tier(user.tier)
        warning = f"\n\n🔒 У тебя уже <b>{cur['name']}</b> — ниже по рангу купить нельзя"
    elif user.balance < tier['price']:
        warning = f"\n\n💰 Не хватает <b>{tier['price'] - user.balance:.0f} ₽</b>"
    text = (
        f"{badge}"
        f"💎 <b>ТАРИФ {tier['name']}</b>\n\n"
        f"📝 {tier['desc']}\n\n"
        f"💵 Цена: <b>{tier['price']} ₽</b>\n"
        f"⏳ Срок: <b>{tier['days']} дней</b>\n\n"
        f"<b>Возможности:</b>\n{features}\n"
        f"{warning}"
    )
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=tier_buy_kb(tier_id))
    await cq.answer()

async def callback_buy(bot: Bot, cq: types.CallbackQuery):
    tier_id = cq.data.split(':')[1]
    tier = get_tier(tier_id)
    user = DB.get_user(cq.from_user.id)
    if not user or not tier:
        await cq.answer("Ошибка", show_alert=True)
        return
    if user.tier == tier_id:
        await cq.answer("У тебя уже есть этот тариф", show_alert=True)
        return
    if user.tier and TIER_RANK[tier_id] < TIER_RANK[user.tier]:
        await cq.answer("Нельзя понижать тариф", show_alert=True)
        return
    if user.balance < tier['price']:
        await cq.answer(f"Не хватает {tier['price']-user.balance:.0f} ₽. Пополни баланс", show_alert=True)
        return
    user.balance -= tier['price']
    code = make_key_code()
    key = DB.add_key(code, tier_id, tier['price'])
    key['bought_by'] = user.uid
    DB.update_key(key)
    user.keys.insert(0, {'code': code, 'tier': tier_id, 'status': 'unused'})
    DB.add_to_user_history(user.uid, {'type':'buy','method':f"Покупка {tier['name']}",'amount':tier['price'],'sign':'-','date':_now()})
    DB.add_transaction(user.uid, 'buy', tier['price'], 'balance', f"Покупка {tier['name']}")
    DB.save_user(user)
    text = (
        f"🎉 <b>ПОКУПКА УСПЕШНА!</b>\n\n"
        f"💎 Тариф: <b>{tier['name']}</b>\n"
        f"💰 Списано: <b>{tier['price']} ₽</b>\n"
        f"💸 Остаток: <b>{user.balance:.2f} ₽</b>\n\n"
        f"🔑 <b>ТВОЙ КЛЮЧ:</b>\n"
        f"<code>{code}</code>\n\n"
        f"📲 Чтобы активировать:\n"
        f"1. Скачай приложение (Профиль → Скачать)\n"
        f"2. Открой → введи ключ → играй!\n\n"
        f"⚠️ Сохрани ключ. Он привяжется к устройству при первой активации."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎫 Активировать сейчас", callback_data="nav:activate")],
        [InlineKeyboardButton(text="📥 Скачать .apk", callback_data="dl:start")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back:home")]
    ])
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await cq.answer("Ключ выдан! 🎉")

def _now():
    return datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
