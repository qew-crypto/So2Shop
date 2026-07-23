import json, os, random, datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.json')

def _load():
    if not os.path.exists(DB_PATH):
        return {"users":{}, "keys":[], "transactions":[], "broadcasts":[], "banned":[], "stats":{"total_activations":0,"total_downloads":0,"total_revenue":0}}
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class User:
    def __init__(self, uid: int, data: dict):
        self.uid = uid
        self.data = data
    @property
    def balance(self): return self.data.get('balance', 0)
    @balance.setter
    def balance(self, v): self.data['balance'] = round(v, 2)
    @property
    def tier(self): return self.data.get('tier', None)
    @tier.setter
    def tier(self, v): self.data['tier'] = v
    @property
    def active_key(self): return self.data.get('active_key', None)
    @property
    def name(self): return self.data.get('name', 'Anonymous')
    @property
    def username(self): return self.data.get('username', '')
    @property
    def reg_date(self): return self.data.get('reg_date', '')
    @property
    def downloads(self): return self.data.get('downloads', 0)
    @property
    def activations(self): return self.data.get('activations', 0)
    @property
    def keys(self): return self.data.get('keys', [])

class DB:
    @staticmethod
    def get_user(uid: int) -> Optional[User]:
        d = _load()
        return User(uid, d['users'].get(str(uid))) if str(uid) in d['users'] else None

    @staticmethod
    def create_user(uid: int, name: str, username: str = '') -> User:
        d = _load()
        d['users'][str(uid)] = {
            'uid': uid, 'name': name, 'username': username,
            'balance': 500, 'tier': None, 'active_key': None,
            'reg_date': datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
            'downloads': 0, 'activations': 0, 'keys': [],
            'history': [], 'last_topup': None
        }
        _save(d)
        return User(uid, d['users'][str(uid)])

    @staticmethod
    def save_user(user: User):
        d = _load()
        d['users'][str(user.uid)] = user.data
        _save(d)

    @staticmethod
    def add_key(code: str, tier: str, price: int) -> dict:
        d = _load()
        key = {'code': code, 'tier': tier, 'price': price,
               'status': 'unused', 'bought_by': None,
               'activated_by': None, 'created_at': datetime.datetime.now().isoformat(),
               'expires': None}
        d['keys'].append(key)
        _save(d)
        return key

    @staticmethod
    def get_key(code: str) -> Optional[dict]:
        d = _load()
        for k in d['keys']:
            if k['code'] == code:
                return k
        return None

    @staticmethod
    def update_key(key: dict):
        d = _load()
        for i, k in enumerate(d['keys']):
            if k['code'] == key['code']:
                d['keys'][i] = key
                break
        _save(d)

    @staticmethod
    def add_transaction(uid: int, ttype: str, amount: float, method: str, desc: str):
        d = _load()
        d['transactions'].append({
            'uid': uid, 'type': ttype, 'amount': amount,
            'method': method, 'desc': desc,
            'date': datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        _save(d)

    @staticmethod
    def get_transactions(uid: int = None, limit: int = 50) -> List[dict]:
        d = _load()
        txs = d['transactions']
        if uid is not None:
            txs = [t for t in txs if t['uid'] == uid]
        return txs[-limit:][::-1]

    @staticmethod
    def get_all_users() -> Dict[str, Any]:
        return _load()['users']

    @staticmethod
    def get_all_keys() -> List[dict]:
        return _load()['keys']

    @staticmethod
    def get_stats() -> dict:
        d = _load()
        users = d['users']
        keys = d['keys']
        txs = d['transactions']
        total_revenue = sum(t['amount'] for t in txs if t['type'] in ('buy','topup'))
        active_users = sum(1 for u in users.values() if u.get('tier'))
        return {
            'total_users': len(users),
            'active_users': active_users,
            'total_keys': len(keys),
            'unused_keys': sum(1 for k in keys if k['status']=='unused'),
            'active_keys': sum(1 for k in keys if k['status']=='active'),
            'total_revenue': total_revenue,
            'total_transactions': len(txs)
        }

    @staticmethod
    def ban(uid: int):
        d = _load()
        if uid not in d['banned']:
            d['banned'].append(uid)
            _save(d)

    @staticmethod
    def unban(uid: int):
        d = _load()
        if uid in d['banned']:
            d['banned'].remove(uid)
            _save(d)

    @staticmethod
    def is_banned(uid: int) -> bool:
        return uid in _load()['banned']

    @staticmethod
    def add_to_user_history(uid: int, entry: dict):
        d = _load()
        u = d['users'].get(str(uid))
        if u:
            u['history'] = u.get('history', [])
            u['history'].insert(0, entry)
            u['history'] = u['history'][:50]
            _save(d)
