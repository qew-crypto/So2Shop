from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from config_loader import TIERS, get_tier

# ====== MAIN MENU (reply) ======
def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 Купить подписку"), KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="🎫 Активировать ключ"), KeyboardButton(text="💳 Пополнить баланс")],
            [KeyboardButton(text="ℹ️ О сервисе"), KeyboardButton(text="📞 Поддержка")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие..."
    )

# ====== TIER PURCHASE ======
def catalog_kb():
    rows = []
    for t in TIERS:
        label = f"{'🔥 ' if t.get('popular') else ''}{t['name']} — {t['price']} ₽"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"tier:{t['id']}")])
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def tier_buy_kb(tier_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Купить и получить ключ", callback_data=f"buy:{tier_id}")],
        [InlineKeyboardButton(text="↩️ К тарифам", callback_data="nav:catalog")]
    ])

# ====== TOPUP ======
def topup_method_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 СБП", callback_data="pay:sbp"),
         InlineKeyboardButton(text="💳 Карта", callback_data="pay:card")],
        [InlineKeyboardButton(text="₿ Крипта (USDT)", callback_data="pay:crypto")],
        [InlineKeyboardButton(text="🎁 Бонус +500 ₽", callback_data="bonus:claim")],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="back:home")]
    ])

def topup_amount_kb(method: str):
    amounts = [100, 300, 500, 1000, 2000, 5000, 10000]
    rows = []
    for i in range(0, len(amounts), 3):
        row = []
        for a in amounts[i:i+3]:
            row.append(InlineKeyboardButton(text=f"{a} ₽", callback_data=f"amt:{a}:{method}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✏️ Своя сумма", callback_data=f"amt:custom:{method}")])
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="nav:topup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ====== PROFILE ======
def profile_kb(active_key: bool = False):
    rows = [[InlineKeyboardButton(text="🎫 Активировать ключ", callback_data="nav:activate")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="nav:topup")],
            [InlineKeyboardButton(text="💎 Купить подписку", callback_data="nav:catalog")]]
    if active_key:
        rows.insert(0, [InlineKeyboardButton(text="📥 Скачать приложение (.apk)", callback_data="dl:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def download_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать standfx_v4.2.1.apk", callback_data="dl:file")],
        [InlineKeyboardButton(text="📷 Получить QR-код", callback_data="dl:qr")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="nav:profile")]
    ])

# ====== ADMIN ======
def admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="adm:users:0")],
        [InlineKeyboardButton(text="🎫 Все ключи", callback_data="adm:keys:0")],
        [InlineKeyboardButton(text="💰 Транзакции", callback_data="adm:tx:0")],
        [InlineKeyboardButton(text="💎 Выдать подписку", callback_data="adm:grant")],
        [InlineKeyboardButton(text="💳 Начислить баланс", callback_data="adm:addbal")],
        [InlineKeyboardButton(text="🚫 Бан / Разбан", callback_data="adm:ban")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm:broadcast")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="adm:promo")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="adm:settings")]
    ])

def admin_users_kb(offset: int, total: int, page_size: int = 8):
    rows = []
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:users:{max(0, offset-page_size)}"))
    nav.append(InlineKeyboardButton(text=f"{offset//page_size+1}/{(total+page_size-1)//page_size}", callback_data="noop"))
    if offset + page_size < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:users:{offset+page_size}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="↩️ Админ-меню", callback_data="adm:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_user_actions_kb(uid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 +баланс", callback_data=f"adm:uadd:{uid}"),
         InlineKeyboardButton(text="🎫 выдать ключ", callback_data=f"adm:ugrant:{uid}")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data=f"adm:uban:{uid}"),
         InlineKeyboardButton(text="⚠️ Предупреждение", callback_data=f"adm:uwarn:{uid}")],
        [InlineKeyboardButton(text="↩️ К списку", callback_data="adm:users:0")]
    ])

def admin_keys_kb(offset: int, total: int, page_size: int = 6):
    rows = [[InlineKeyboardButton(text=f"🔑 Сгенерировать новый (VIP)", callback_data="adm:keygen:VIP")],
            [InlineKeyboardButton(text=f"🔑 Сгенерировать BASE", callback_data="adm:keygen:BASE"),
             InlineKeyboardButton(text=f"🔑 Сгенерировать PREMIUM", callback_data="adm:keygen:PREMIUM")]]
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:keys:{max(0, offset-page_size)}"))
    nav.append(InlineKeyboardButton(text=f"{offset//page_size+1}/{(total+page_size-1)//page_size}", callback_data="noop"))
    if offset + page_size < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:keys:{offset+page_size}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="↩️ Админ-меню", callback_data="adm:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_broadcast_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Всем пользователям", callback_data="adm:bc:all")],
        [InlineKeyboardButton(text="💎 Активным подписчикам", callback_data="adm:bc:active")],
        [InlineKeyboardButton(text="🌟 VIP/PREMIUM", callback_data="adm:bc:top")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:home")]
    ])

def confirm_kb(action: str, data: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{action}:{data}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="adm:home")]
    ])
