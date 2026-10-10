import ast
import copy
import sys
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail

class FakeModel:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)

class FastAPI:
    def __init__(self): self.routes = []
    def add_event_handler(self, *args): pass
    def _route(self, path, method):
        def add(fn):
            self.routes.append(NS(path=path, methods=[method], endpoint=fn))
            return fn
        return add
    def get(self, path): return self._route(path, 'GET')
    def post(self, path): return self._route(path, 'POST')

# Execute production service unchanged, replacing only framework declarations.
source = Path(__file__).resolve().parents[1] / 'kabutar_discovery.py'
tree = ast.parse(source.read_text())
tree.body = [n for n in tree.body if not isinstance(n, ast.ImportFrom) or n.module not in ('fastapi', 'fastapi.responses', 'pydantic')]
namespace = {'__name__': 'discovery_test', 'HTTPException': HTTPException, 'Request': object,
             'JSONResponse': lambda data, **kwargs: data, 'BaseModel': FakeModel,
             'Field': lambda default=None, **kwargs: default}
exec(compile(tree, str(source), 'exec'), namespace)
DiscoveryService, DiscoverySettings, nickname_value, parse_lookup, public_card, register_discovery = [namespace[name] for name in
    ('DiscoveryService', 'DiscoverySettings', 'nickname_value', 'parse_lookup', 'public_card', 'register_discovery')]


class Duplicate(Exception):
    pgcode = '23505'


class Cursor:
    def __init__(self, db): self.db, self.row = db, None
    def execute(self, sql, args=()):
        self.db.queries.append((sql, args))
        q = ' '.join(sql.split())
        self.row = None
        if 'SELECT u.kabutar_nickname,u.phone_discoverable,t.phone,t.verified_at' in q:
            user = self.db.users.get(args[0])
            if user:
                identity = self.db.identities.get(args[0], {})
                self.row = {**user, **identity}
        elif q.startswith('UPDATE users SET kabutar_nickname='):
            nickname, optin, uid = args
            if nickname and any(u.get('kabutar_nickname', '').lower() == nickname for other, u in self.db.users.items() if other != uid and u.get('kabutar_nickname')):
                raise Duplicate()
            self.db.users[uid].update(kabutar_nickname=nickname, phone_discoverable=optin)
        elif q.startswith('SELECT u.user_id,u.full_name,u.role,u.kabutar_id'):
            for uid, user in self.db.users.items():
                if 'JOIN kabutar_telegram_identity' in q:
                    identity = self.db.identities.get(uid, {})
                    matches = identity.get('phone') == args[0] and identity.get('verified_at') and user.get('phone_discoverable')
                elif 'LOWER(u.kabutar_nickname)' in q:
                    matches = (user.get('kabutar_nickname') or '').lower() == args[0]
                else:
                    matches = user.get('kabutar_id') == args[0]
                if matches:
                    self.row = {**user, 'user_id': uid, 'rasm_bormi': True}
                    break
    def fetchone(self): return copy.deepcopy(self.row)


class Database:
    def __init__(self):
        self.users = {
            1: dict(full_name='Men', role='kabutar', kabutar_id='KB-12345678', kabutar_nickname=None, phone_discoverable=False),
            -2: dict(full_name='Google foydalanuvchi', role='oquvchi', kabutar_id='KB-98765432', kabutar_nickname='ali_2000', phone_discoverable=False),
            3: dict(full_name='Ustoz', role='oqituvchi', kabutar_id='KB-123456', kabutar_nickname='ustoz_1', phone_discoverable=True),
        }
        self.identities = {
            1: dict(phone='+998901111111', verified_at=datetime.now(timezone.utc)),
            3: dict(phone='+998903333333', verified_at=datetime.now(timezone.utc)),
        }
        self.queries = []


class Auth:
    def __init__(self, db): self.db, self.locked = db, []
    @contextmanager
    def transaction(self):
        before = copy.deepcopy(self.db.users)
        try: yield Cursor(self.db)
        except Exception:
            self.db.users = before
            raise
    def user_lock(self, cur, uid): self.locked.append(uid)
    def claims(self, token): return {'admin_korish': 999} if token == 'view' else {}
    def rate(self, *args): pass
    def ip(self, request): return '127.0.0.1'
    def origin(self, request): pass


def request(token=None, method='GET'):
    return NS(headers={} if token is None else {'authorization': token}, method=method)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.auth = Auth(self.db)
        self.platform = NS(_jwt_tekshir=lambda token: 1, _kabutar_id_ber=lambda cur, uid: self.db.users[uid]['kabutar_id'])
        self.service = DiscoveryService(self.platform, self.auth)
    def assert_http(self, status, callback, *args, **kwargs):
        with self.assertRaises(HTTPException) as cm: callback(*args, **kwargs)
        self.assertEqual(cm.exception.status_code, status)
        return cm.exception.detail

    def test_nickname_case_and_boundaries(self):
        self.assertEqual(nickname_value(' @Ali_2000 '), 'ali_2000')
        self.assertIsNone(nickname_value(''))
        self.assertEqual(nickname_value('a' * 32), 'a' * 32)
        for bad in ('abcd', 'a' * 33, '1abcde', '_abcde', 'ali-test', 'али123', 'ábcdef'):
            self.assert_http(422, nickname_value, bad)

    def test_exact_query_parsing_no_partial_phone_or_free_name(self):
        self.assertEqual(parse_lookup('kb-12345678'), ('kabutar_id', 'KB-12345678'))
        self.assertEqual(parse_lookup('1234567890'), ('kabutar_id', 'KB-1234567890'))
        self.assertEqual(parse_lookup('@ALI_2000'), ('nickname', 'ali_2000'))
        self.assertEqual(parse_lookup('+998 (90) 333-33-33'), ('phone', '+998903333333'))
        for bad in ('Ali Vali', '+99890', '+998901234567%', '@ali%', 'KB-１２３４５６', '', 'x' * 81):
            self.assert_http(422, parse_lookup, bad)

    def test_negative_google_id_supported_without_phone_exposure(self):
        card = self.service.find(1, '@ALI_2000')
        self.assertEqual(card['user_id'], -2)
        self.assertEqual(card['kabutar_id'], 'KB-98765432')
        self.assertNotIn('phone', card)
        self.assertNotIn('phone_masked', card)
        self.assertEqual(card['rollar'][0]['muassasa'], '')

    def test_phone_hidden_by_default_even_if_verified(self):
        self.assert_http(404, self.service.find, 3, '+998901111111')

    def test_optin_verified_phone_lookup_then_revocation(self):
        card = self.service.find(1, '+998903333333')
        self.assertEqual(card['user_id'], 3)
        self.service.update(3, DiscoverySettings(nickname='ustoz_1', phone_discoverable=False))
        self.assert_http(404, self.service.find, 1, '+998903333333')
        self.assertEqual(self.service.find(1, '@ustoz_1')['user_id'], 3)

    def test_unverified_cannot_optin_and_legacy_phone_alone_is_insufficient(self):
        self.assert_http(422, self.service.update, -2, DiscoverySettings(nickname='ali_2000', phone_discoverable=True))
        self.db.identities[-2] = {'phone': '+998902222222', 'verified_at': None}
        self.db.users[-2]['phone_discoverable'] = True
        self.assert_http(404, self.service.find, 1, '+998902222222')
        self.assert_http(422, self.service.update, -2, DiscoverySettings(nickname='ali_2000', phone_discoverable=True))

    def test_missing_private_unverified_phone_same_response(self):
        missing = self.assert_http(404, self.service.find, 3, '+998909999999')
        private = self.assert_http(404, self.service.find, 3, '+998901111111')
        self.assertEqual(missing, private)

    def test_unique_nickname_conflict_and_rollback(self):
        self.assert_http(409, self.service.update, 1, DiscoverySettings(nickname='ALI_2000'))
        self.assertIsNone(self.db.users[1]['kabutar_nickname'])

    def test_profile_returns_mask_only_and_explicit_optin(self):
        result = self.service.update(1, DiscoverySettings(nickname='aziz_1', phone_discoverable=True))
        self.assertEqual(result['nickname'], 'aziz_1')
        self.assertTrue(result['phone_verified'])
        self.assertTrue(result['phone_discoverable'])
        self.assertNotIn('+998901111111', str(result))
        self.assertIn(1, self.auth.locked)

    def test_self_match_and_authorization(self):
        self.assert_http(400, self.service.find, 1, 'KB-12345678')
        self.assert_http(401, self.service.actor, request())
        self.assert_http(401, self.service.actor, request('Basic token'))
        self.assertEqual(self.service.actor(request('Bearer token')), 1)
        self.assert_http(403, self.service.actor, request('Bearer view'), mutate=True)

    def test_public_card_drops_sensitive_fields_and_admin_claim(self):
        row = dict(user_id=-55, full_name='Ism', role='admin', phone='+998901234567', telegram_id=42,
                   school='Private', family='Private', kabutar_nickname='name_1')
        card = public_card(row)
        self.assertEqual(card['qisqa'], 'Kabutar foydalanuvchisi')
        self.assertFalse({'phone', 'telegram_id', 'school', 'family'} & card.keys())

    def test_only_bounded_routes_registered(self):
        app = FastAPI()
        register_discovery(app, self.platform, self.auth)
        routes = {(route.path, tuple(sorted(route.methods))) for route in app.routes if route.path.startswith(('/auth/', '/api/'))}
        self.assertEqual(routes, {('/auth/profile/discovery', ('GET',)), ('/auth/profile/discovery', ('POST',)), ('/api/kabutar/find', ('GET',))})


if __name__ == '__main__': unittest.main()
