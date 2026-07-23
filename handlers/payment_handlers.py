import random
from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import DB
from config_loader import CFG, TIERS

async def callback_pay_method(bot: Bot, cq: types.CallbackQuery):
    method = cq.data.split(':')[1]
    methods = {'sbp':'📱 СБП (по номеру)','card':'💳 Банковская карта','crypto':'₿ Крипта (USDT TRC-20)'}
    method_name = methods.get(method, method)
    text = (
        f"<b>{method_name}</b>\n\n"
        f"💵 Выбери сумму пополнения:\n"
        f"💡 <i>Чем больше сумма — тем выгоднее!</i>\n\n"
        f"🎁 Акция: при пополнении от 1000 ₽ — бонус +10%\n"
        f"⚠️ DEMO-режим: деньги не списываются"
    )
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML,
                               reply_markup=__import__('middlewares.keyboards', fromlist=['']).topup_amount_kb(method))
    await cq.answer()

async def callback_pay_amount(bot: Bot, cq: types.CallbackQuery):
    _, amount_str, method = cq.data.split(':')
    user = DB.get_user(cq.from_user.id) or DB.create_user(cq.from_user.id, cq.from_user.first_name or 'P')
    if amount_str == 'custom':
        await cq.message.edit_text(
            "✏️ <b>Своя сумма</b>\n\n"
            "Введи сумму для пополнения (от 50 до 50000 ₽):\n\n"
            "💡 <i>Минимум 50 ₽, максимум 50 000 ₽</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data="nav:topup")]
            ])
        )
        DB.save_user(user)
        await cq.answer()
        return
    amt = int(amount_str)
    # имитация платежа через "обработку"
    if method == 'crypto':
        # крипта в долларах, конвертация
        added_rub = round(amt * 90)
    else:
        added_rub = amt
        if amt >= 1000: added_rub = round(amt * 1.10)
    user.balance += added_rub
    DB.add_to_user_history(user.uid, {
        'type':'topup','method':{'sbp':'СБП','card':'Карта','crypto':'USDT'}[method],
        'amount':added_rub,'sign':'+','date':_now()
    })
    DB.add_transaction(user.uid, 'topup', added_rub, method, 'Пополнение баланса')
    DB.save_user(user)
    methods_names = {'sbp':'СБП','card':'Банковская карта','crypto':'USDT TRC-20'}
    text = (
        f"✅ <b>БАЛАНС ПОПОЛНЕН!</b>\n\n"
        f"💳 Способ: {methods_names[method]}\n"
        f"💵 Зачислено: <b>+{added_rub:.0f} ₽</b>\n"
        f"💰 Текущий баланс: <b>{user.balance:.2f} ₽</b>\n\n"
        f"{'🎁 Бонус +10% применён!' if method!='crypto' and amt>=1000 else ''}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="nav:catalog")],
        [InlineKeyboardButton(text="💳 Пополнить ещё", callback_data="nav:topup")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back:home")]
    ])
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await cq.answer(f"✅ +{added_rub:.0f} ₽")

async def callback_bonus_claim(bot: Bot, cq: types.CallbackQuery):
    user = DB.get_user(cq.from_user.id) or DB.create_user(cq.from_user.id, cq.from_user.first_name or 'P')
    # бонус раз в день
    last = user.data.get('last_bonus')
    from datetime import datetime, timedelta
    today = datetime.now().date().isoformat()
    if last == today:
        await cq.answer("🎁 Бонус уже получен сегодня. Приходи завтра!", show_alert=True)
        return
    user.data['last_bonus'] = today
    user.balance += 100
    DB.add_to_user_history(user.uid, {'type':'bonus','method':'Ежедневный бонус','amount':100,'sign':'+','date':_now()})
    DB.add_transaction(user.uid, 'bonus', 100, 'system', 'Ежедневный бонус')
    DB.save_user(user)
    text = (
        f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС +100 ₽</b>\n\n"
        f"💰 Зачислено!\n"
        f"💸 Баланс: <b>{user.balance:.2f} ₽</b>\n\n"
        f"⏰ Следующий бонус через: до конца дня 🕐\n\n"
        f"💡 Не забывай заходить каждый день!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="nav:catalog")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back:home")]
    ])
    await cq.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await cq.answer("+100 ₽ 🎁")

def _now():
    from datetime import datetime
    return datetime.now().strftime('%d.%m.%Y %H:%M')
