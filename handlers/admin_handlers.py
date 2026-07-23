from aiogram import Bot, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DB, User
from config_loader import ADMIN_IDS, TIERS, get_tier
from middlewares.keyboards import (
    admin_main_kb, admin_users_kb, admin_user_actions_kb,
    admin_keys_kb, admin_broadcast_kb
)
from datetime import datetime
import random, string

PAGE_USERS = 8
PAGE_KEYS = 6
PAGE_TX = 8

class AdminStates(StatesGroup):
    waiting_uid = State()
    waiting_addbal = State()
    waiting_grant_tier = State()
    waiting_grant_uid = State()
    waiting_ban_uid = State()
    waiting_broadcast = State()
    waiting_promo_name = State()
    waiting_promo_amount = State()
    waiting_promo_uses = State()
    waiting_keygen = State()

def admin_only(handler):
    async def wrapper(bot: Bot, cq_or_msg, *args, **kwargs):
        uid = cq_or_msg.from_user.id
        if uid not in ADMIN_IDS:
            if hasattr(cq_or_msg, 'answer'):
                try: await cq_or_msg.answer("⛔ Доступ запрещён", show_alert=True)
                except: pass
            return
        return await handler(bot, cq_or_msg, *args, **kwargs)
    return wrapper

# ===== STATS =====
@admin_only
async def adm_stats(bot: Bot, cq: types.CallbackQuery):
    s = DB.get_stats()
    text = (
        "📊 <b>СТАТИСТИКА СЕРВИСА</b>\n\n"
        f"👥 Всего пользователей: <b>{s['total_users']}</b>\n"
        f"💎 Активных подписчиков: <b>{s['active_users']}</b>\n"
        f"🎫 Всего ключей: <b>{s['total_keys']}</b>\n"
        f"  ├ ○ Не активированы: <b>{s['unused_keys']}</b>\n"
        f"  └ ● Активны: <b>{s['active_keys']}</b>\n"
        f"💰 Общий оборот: <b>{s['total_revenue']:.2f} ₽</b>\n"
        f"📋 Транзакций: <b>{s['total_transactions']}</b>\n\n"
        f"⏰ <i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
    )
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_main_kb())
    await cq.answer()

# ===== USERS LIST =====
@admin_only
async def adm_users(bot: Bot, cq: types.CallbackQuery):
    offset = int(cq.data.split(':')[2]) if cq.data.count(':')>=2 else 0
    users = list(DB.get_all_users().values())
    total = len(users)
    page = users[offset:offset+PAGE_USERS]
    text = f"👥 <b>ПОЛЬЗОВАТЕЛИ</b> ({total} всего)\n\n"
    for u in page:
        name = u.get('name','—')
        username = f"@{u.get('username','')}" if u.get('username') else ''
        tier = u.get('tier') or '🔓 нет'
        bal = u.get('balance',0)
        text += f"🆔 <code>{u['uid']}</code> — <b>{name}</b> {username}\n   💎 {tier} | 💰 {bal:.2f}₽\n\n"
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_users_kb(offset, total, PAGE_USERS))
    await cq.answer()

# ===== USER ACTIONS =====
@admin_only
async def adm_user_action(bot: Bot, cq: types.CallbackQuery):
    parts = cq.data.split(':')
    action = parts[1]
    uid = int(parts[2])
    users = DB.get_all_users()
    user_data = users.get(str(uid))
    if not user_data:
        await cq.answer("Юзер не найден", show_alert=True)
        return
    if action == 'add':
        await cq.message.edit_text(
            f"💳 <b>НАЧИСЛЕНИЕ БАЛАНСА</b>\n\n"
            f"Юзер: <code>{uid}</code>\n\n"
            f"Введи сумму для начисления (можно отрицательную для списания):",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Отмена", callback_data="adm:users:0")]
            ])
        )
        bot._adm_state = ('addbal', uid)
        await cq.answer()
    elif action == 'grant':
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{t['name']} ({t['price']}₽)", callback_data=f"adm:grantt:{t['id']}:{uid}")]
            for t in TIERS
        ])
        kb.inline_keyboard.append([InlineKeyboardButton(text="↩️ Отмена", callback_data="adm:users:0")])
        await cq.message.edit_text(
            f"🎫 <b>ВЫДАТЬ ТАРИФ</b>\n\n"
            f"Юзер: <code>{uid}</code>\nВыбери тариф:",
            parse_mode=ParseMode.HTML, reply_markup=kb
        )
        await cq.answer()
    elif action == 'ban':
        DB.ban(uid)
        await cq.answer(f"🚫 Юзер {uid} забанен", show_alert=True)
        await adm_users(bot, types.CallbackQuery(id=cq.id, from_user=cq.from_user, chat_instance=cq.chat_instance, message=cq.message, data="adm:users:0"))
    elif action == 'warn':
        try:
            await bot.send_message(uid, "⚠️ <b>Предупреждение от администратора</b>\n\nПожалуйста, соблюдай правила сервиса.", parse_mode=ParseMode.HTML)
            await cq.answer("Отправлено ✅", show_alert=True)
        except: await cq.answer("Не удалось отправить", show_alert=True)

@admin_only
async def adm_grant_tier(bot: Bot, cq: types.CallbackQuery):
    parts = cq.data.split(':')
    tier_id, uid = parts[1], int(parts[2])
    tier = get_tier(tier_id)
    if not tier: return
    user_data = DB.get_all_users().get(str(uid))
    if not user_data:
        await cq.answer("Юзер не найден", show_alert=True)
        return
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4)) + '-' + ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=12))
    code = '-'.join([code.replace('-','')[i:i+4] for i in range(0,16,4)])
    key = DB.add_key(code, tier_id, tier['price'])
    key['bought_by'] = uid
    DB.update_key(key)
    user = User(uid, user_data)
    user.keys.insert(0, {'code': code, 'tier': tier_id, 'status': 'unused', 'price': tier['price'], 'given_by_admin': True})
    DB.save_user(user)
    DB.add_transaction(uid, 'admin_grant', 0, 'admin', f"Админ-выдача {tier['name']}")
    try:
        await bot.send_message(uid, f"🎁 <b>ПОДАРОК ОТ АДМИНИСТРАЦИИ!</b>\n\nВам выдан тариф <b>{tier['name']}</b>!\n\n🔑 Ваш ключ:\n<code>{code}</code>\n\nАктивируйте его командой /activate", parse_mode=ParseMode.HTML)
    except: pass
    await cq.message.edit_text(
        f"✅ <b>ТАРИФ ВЫДАН</b>\n\n"
        f"👤 Юзер: <code>{uid}</code>\n"
        f"💎 Тариф: <b>{tier['name']}</b>\n"
        f"🔑 Ключ: <code>{code}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_main_kb()
    )
    await cq.answer("Выдано ✅")

@admin_only
async def adm_add_bal(bot: Bot, cq: types.CallbackQuery):
    bot._adm_state = ('addbal', int(cq.data.split(':')[2]))
    await cq.message.edit_text(
        f"💳 <b>НАЧИСЛЕНИЕ БАЛАНСА</b>\n\n"
        f"Юзер: <code>{cq.data.split(':')[2]}</code>\n\n"
        f"Введи сумму (целое число):",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="adm:users:0")]
        ])
    )
    await cq.answer()

# ===== KEYS =====
@admin_only
async def adm_keys(bot: Bot, cq: types.CallbackQuery):
    offset = int(cq.data.split(':')[2]) if cq.data.count(':')>=2 else 0
    keys = DB.get_all_keys()
    keys_rev = keys[::-1]
    total = len(keys_rev)
    page = keys_rev[offset:offset+PAGE_KEYS]
    text = f"🎫 <b>ВСЕ КЛЮЧИ</b> ({total} всего)\n\n"
    for k in page:
        icon = '○' if k['status']=='unused' else '●'
        text += f"{icon} <code>{k['code']}</code> — {k['tier']}\n   status: <b>{k['status']}</b>\n"
    if not page: text += "Пусто.\n"
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_keys_kb(offset, total, PAGE_KEYS))
    await cq.answer()

@admin_only
async def adm_keygen(bot: Bot, cq: types.CallbackQuery):
    tier_id = cq.data.split(':')[2]
    tier = get_tier(tier_id)
    if not tier: return
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    code_chars = []
    for i in range(16):
        code_chars.append(random.choice(chars))
    code = '-'.join([''.join(code_chars[i:i+4]) for i in range(0,16,4)])
    key = DB.add_key(code, tier_id, tier['price'])
    await cq.message.edit_text(
        f"✅ <b>КЛЮЧ СОЗДАН</b>\n\n"
        f"💎 Тариф: <b>{tier['name']}</b>\n"
        f"🔑 Ключ: <code>{code}</code>\n\n"
        f"Можешь отправить юзеру вручную или использовать в выдаче.",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_keys_kb(0, len(DB.get_all_keys()), PAGE_KEYS)
    )
    await cq.answer("Ключ создан 🎉")

# ===== TRANSACTIONS =====
@admin_only
async def adm_tx(bot: Bot, cq: types.CallbackQuery):
    offset = int(cq.data.split(':')[2]) if cq.data.count(':')>=2 else 0
    txs = DB.get_transactions(limit=200)
    total = len(txs)
    page = txs[offset:offset+PAGE_TX]
    text = f"💰 <b>ТРАНЗАКЦИИ</b> ({total} всего)\n\n"
    icon_map = {'buy':'🛒','topup':'💳','activate':'🔓','bonus':'🎁','admin_grant':'🎖'}
    for t in page:
        icon = icon_map.get(t['type'], '•')
        text += f"{icon} <code>{t['uid']}</code> — {t['amount']:.0f}₽ {t['method']}\n   <i>{t['date']}</i>\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    nav = []
    if offset > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:tx:{max(0,offset-PAGE_TX)}"))
    nav.append(InlineKeyboardButton(text=f"{offset//PAGE_TX+1}", callback_data="noop"))
    if offset+PAGE_TX<total: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:tx:{offset+PAGE_TX}"))
    kb.inline_keyboard.append(nav)
    kb.inline_keyboard.append([InlineKeyboardButton(text="↩️ Админ", callback_data="adm:home")])
    if not page: text += "Пусто.\n"
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await cq.answer()

# ===== BROADCAST =====
@admin_only
async def adm_bc_start(bot: Bot, cq: types.CallbackQuery):
    await cq.message.edit_text("📢 <b>РАССЫЛКА</b>\n\nВыбери аудиторию:", parse_mode=ParseMode.HTML, reply_markup=admin_broadcast_kb())
    await cq.answer()

@admin_only
async def adm_bc_audience(bot: Bot, cq: types.CallbackQuery):
    audience = cq.data.split(':')[2]
    bot._bc_audience = audience
    bot._bc_state = True
    await cq.message.edit_text(
        f"📢 <b>РАССЫЛКА → {audience.upper()}</b>\n\n"
        f"Введи текст сообщения (можно с HTML разметкой):\n\n"
        f"💡 Можно использовать: <code>&lt;b&gt;</code>, <code>&lt;i&gt;</code>, <code>&lt;code&gt;</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:home")]
        ])
    )
    await cq.answer()

# ===== MAIN =====
@admin_only
async def adm_home(bot: Bot, cq: types.CallbackQuery):
    s = DB.get_stats()
    text = (
        f"🎛 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"📊 Юзеров: {s['total_users']} | Активных: {s['active_users']}\n"
        f"💰 Оборот: {s['total_revenue']:.0f} ₽\n\n"
        f"Выбери действие:"
    )
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_main_kb())
    await cq.answer()

# ===== ADMIN COMMAND =====
async def cmd_admin(bot: Bot, message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещён")
        return
    s = DB.get_stats()
    text = (
        f"🎛 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"📊 Юзеров: {s['total_users']} | Активных: {s['active_users']}\n"
        f"💰 Оборот: {s['total_revenue']:.0f} ₽\n\n"
        f"Выбери действие:"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=admin_main_kb())
