import json, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

CFG = load_config()

BOT_TOKEN = CFG.get('BOT_TOKEN', '')
ADMIN_IDS = CFG.get('ADMIN_IDS', [])
START_BALANCE = CFG.get('START_BALANCE', 500)
CURRENCY = CFG.get('CURRENCY', '₽')
SUPPORT = CFG.get('SUPPORT_CONTACT', '@support')
CHANNEL = CFG.get('CHANNEL_LINK', '')
VERSION = CFG.get('VERSION', '4.2.1')
DEMO_MODE = CFG.get('DEMO_MODE', True)

TIERS = [
    {
        'id': 'BASE', 'name': 'BASE', 'price': 199, 'days': 30,
        'desc': 'Базовый тариф на 30 дней. Все основные функции.',
        'features': [
            '🎯 Aimbot (FOV, smoothing)',
            '🔫 Triggerbot',
            '👁️ ESP / Wallhack',
            '🎨 Skin Changer (5 пушек)',
            '💥 No Recoil',
            '🛡️ Anti-Ban Shield'
        ]
    },
    {
        'id': 'VIP', 'name': 'VIP', 'price': 499, 'days': 30, 'popular': True,
        'desc': 'Хит продаж! Полный доступ на 30 дней.',
        'features': [
            '🎯 Aimbot Pro (все настройки)',
            '🔫 Triggerbot Pro',
            '👁️ ESP / Wallhack Pro',
            '🎨 Skin Changer (все пушки)',
            '💥 No Recoil',
            '🛡️ Anti-Ban Shield Pro',
            '📡 Radar Hack',
            '🪄 Magic Bullet',
            '⚙️ In-Game Menu (full)'
        ]
    },
    {
        'id': 'PREMIUM', 'name': 'PREMIUM', 'price': 1299, 'days': 90,
        'desc': 'Лучший тариф на 90 дней. Максимум возможностей.',
        'features': [
            '🎯 Aimbot Pro (все настройки)',
            '🔫 Triggerbot Pro',
            '👁️ ESP / Wallhack Pro',
            '🎨 Skin Changer (все пушки)',
            '💥 No Recoil',
            '🛡️ Anti-Ban Shield Pro',
            '📡 Radar Hack',
            '🪄 Magic Bullet (unlimited)',
            '⚙️ In-Game Menu (full)',
            '🌟 Приоритетная поддержка',
            '🎁 Эксклюзивный Discord-роль'
        ]
    }
]

TIER_RANK = {'BASE': 1, 'VIP': 2, 'PREMIUM': 3}

def get_tier(tier_id):
    for t in TIERS:
        if t['id'] == tier_id:
            return t
    return None
