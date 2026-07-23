from aiogram import Bot, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import DB
from config_loader import get_tier
from datetime import datetime, timedelta

class ActivateState(StatesGroup):
    waiting_code = State()

async def callback_nav_activate(bot: Bot, cq: types.CallbackQuery):
    await cq.message.edit_text(
        "🎫 <b>АКТИВАЦИЯ КЛЮЧА</b>\n\n"
        "📨 Введи ключ в формате <code>XXXX-XXXX-XXXX-XXXX</code>\n\n"
        "💡 <i>Ключ привязывается к устройству. Один ключ = одно устройство.</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="nav:profile")]
        ])
    )
    await cq.answer()

async def cmd_activate(bot: Bot, message: types.Message):
    await message.answer(
        "🎫 <b>АКТИВАЦИЯ КЛЮЧА</b>\n\n"
        "📨 Введи ключ в формате <code>XXXX-XXXX-XXXX-XXXX</code>",
        parse_mode=ParseMode.HTML
    )

async def process_activate(bot: Bot, message: types.Message):
    code = message.text.strip().upper()
    # маска: если ввели без дефисов — добавим
    if '-' not in code:
        clean = ''.join(c for c in code if c.isalnum())[:16]
        code = '-'.join([clean[i:i+4] for i in range(0, len(clean), 4)])

    if len(code) != 19 or code.count('-') != 3:
        await message.answer("❌ <b>Неверный формат</b>\nНужно: <code>XXXX-XXXX-XXXX-XXXX</code>", parse_mode=ParseMode.HTML)
        return

    key = DB.get_key(code)
    user = DB.get_user(message.from_user.id)

    if not key:
        await message.answer("❌ <b>Ключ не найден</b>\nПроверь правильность или купи подписку.", parse_mode=ParseMode.HTML)
        return
    if key['status'] == 'active':
        await message.answer("⚠️ <b>Этот ключ уже активирован</b>\nКаждый ключ работает на одном устройстве.", parse_mode=ParseMode.HTML)
        return
    if key['bought_by'] and key['bought_by'] != message.from_user.id:
        # мягкая проверка: предупреждаем, но не блокируем (демо)
        pass

    tier = get_tier(key['tier'])
    days = tier['days'] if tier else 30
    expires = datetime.now() + timedelta(days=days)
    key['status'] = 'active'
    key['activated_by'] = message.from_user.id
    key['expires'] = expires.isoformat()
    DB.update_key(key)

    if user:
        user.tier = key['tier']
        user.activations += 1
        user.data['active_key'] = code
        # найдём ключ в списке юзера и пометим
        for k in user.keys:
            if k['code'] == code:
                k['status'] = 'active'
        DB.add_to_user_history(user.uid, {'type':'activate','method':f"Активация {code}",'amount':0,'sign':'•','date':_now()})
        DB.save_user(user)

    DB.add_transaction(message.from_user.id, 'activate', 0, 'system', f"Активация {code}")
    text = (
        f"✅ <b>КЛЮЧ АКТИВИРОВАН!</b>\n\n"
        f"💎 Тариф: <b>{tier['name']}</b>\n"
        f"⏳ Активен до: <b>{expires.strftime('%d.%m.%Y')}</b>\n"
        f"📥 Теперь можешь скачать приложение\n\n"
        f"⬇️ Скачай standfx_apk в профиле!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать .apk", callback_data="dl:start")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="nav:profile")]
    ])
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def callback_dl_start(bot: Bot, cq: types.CallbackQuery):
    user = DB.get_user(cq.from_user.id)
    if not user or not user.active_key:
        await cq.message.edit_text(
            "🔒 <b>Скачивание недоступно</b>\n\n"
            "Сначала купи и активируй ключ.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Купить тариф", callback_data="nav:catalog")],
                [InlineKeyboardButton(text="🏠 Главная", callback_data="back:home")]
            ])
        )
        await cq.answer()
        return
    text = (
        "📥 <b>СКАЧИВАНИЕ ПРИЛОЖЕНИЯ</b>\n\n"
        "📱 <b>standfx_v4.2.1.apk</b>\n"
        "📦 Размер: 12.4 MB\n"
        "🤖 Android 8.0+\n"
        "⚡ Без рут-прав\n\n"
        "⚠️ Перед установкой:\n"
        "• Включи установку из неизвестных источников\n"
        "• Отключи антивирус (он может видеть чит как угрозу)\n\n"
        "🔐 Тип подписки: <b>" + (user.tier or '—') + "</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇ Скачать APK", callback_data="dl:file")],
        [InlineKeyboardButton(text="📷 Показать QR", callback_data="dl:qr")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="nav:profile")]
    ])
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await cq.answer()

async def callback_dl_file(bot: Bot, cq: types.CallbackQuery):
    user = DB.get_user(cq.from_user.id)
    if not user or not user.active_key:
        await cq.answer("Нет активной подписки", show_alert=True)
        return
    user.downloads += 1
    DB.save_user(user)
    await cq.message.answer(
        "✅ <b>Файл отправлен!</b>\n\n"
        "📥 <code>standfx_v4.2.1.apk</code>\n"
        "(демо: реальный файл не прикреплён)\n\n"
        "📊 Скачиваний у тебя: <b>" + str(user.downloads) + "</b>",
        parse_mode=ParseMode.HTML
    )
    await cq.answer("📥 Отправлено")

async def callback_dl_qr(bot: Bot, cq: types.CallbackQuery):
    await cq.message.answer(
        "📷 <b>QR-КОД ДЛЯ СКАЧИВАНИЯ</b>\n\n"
        "В демо-режиме QR не генерируется.\n"
        "В рабочей версии здесь будет QR с прямой ссылкой на .apk\n\n"
        "💡 Открой сайт @standfx_webbot чтобы получить QR автоматически.",
        parse_mode=ParseMode.HTML
    )
    await cq.answer()

def _now():
    return datetime.now().strftime('%d.%m.%Y %H:%M')
