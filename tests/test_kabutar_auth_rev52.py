"""Actual auth handlers against the transactional fake DB, without network APIs."""
import os
import types
import unittest
from unittest.mock import patch

from tests import test_kabutar_auth_rev31 as fixtures

A = fixtures.A
FakeApp = fixtures.FakeApp


class TelegramSiteTests(unittest.TestCase):
    setUp = fixtures.AuthTests.setUp
    assert_http = fixtures.AuthTests.assert_http
    confirm_body = fixtures.AuthTests.confirm_body

    def start(self, request=None):
        return self.app.routes['/auth/telegram/start'](
            types.SimpleNamespace(mode='login', token=None), request or self.request)

    def inspect(self, challenge):
        return self.app.routes['/auth/telegram/inspect'](
            types.SimpleNamespace(challenge=challenge), 's' * 32)

    def test_actual_browser_site_survives_stale_backend_default(self):
        self.p.FRONTEND_URL = 'https://old-deployment.up.railway.app'
        result = self.start()
        inspected = self.inspect(result['challenge'])
        self.assertEqual(inspected['site'], 'https://talimkabutar.uz')
        self.assertEqual(inspected['verification_code'], result['verification_code'])
        self.assertNotIn('browser_secret', inspected)
        self.assertNotIn(result['browser_secret'], result['bot_url'])

    def test_complete_new_challenge_keeps_browser_proof_and_single_session(self):
        result = self.start()
        body = types.SimpleNamespace(challenge=result['challenge'], telegram_user_id=111,
            contact_user_id=111, phone='+998901234567', full_name='Teacher')
        self.app.routes['/auth/telegram/confirm'](body, 's' * 32)
        browser = types.SimpleNamespace(challenge=result['challenge'], browser_secret=result['browser_secret'])
        login = self.app.routes['/auth/telegram/poll'](browser, self.request)
        retry = self.app.routes['/auth/telegram/poll'](browser, self.request)
        self.assertEqual(login, retry)
        self.assertEqual(self.p._jwt_tekshir(login['token']), 111)
        self.assertEqual(len(self.db.state['sessions']), 1)

    def test_attacker_origin_does_not_create_challenge(self):
        before = len(self.db.state['challenges'])
        request = types.SimpleNamespace(headers={'origin':'https://attacker.example'}, client=self.request.client)
        self.assert_http(403, self.start, request)
        self.assertEqual(len(self.db.state['challenges']), before)

    def test_headerless_request_uses_configured_site_not_forwarded_host(self):
        request = types.SimpleNamespace(headers={'x-forwarded-host':'attacker.example',
            'host':'attacker.example'}, client=self.request.client)
        result = self.start(request)
        self.assertEqual(self.inspect(result['challenge'])['site'], 'https://talimkabutar.uz')

    def test_old_pending_challenge_uses_legacy_configured_origin(self):
        self.assertEqual(self.inspect(self.challenge)['site'], 'https://talimkabutar.uz')

    def test_site_does_not_contain_credentials_or_path(self):
        for value in ('https://person:secret@example.com', 'https://example.com/api',
                      'https://example.com?key=secret', 'https://example.com#secret', 'javascript:alert(1)'):
            self.assertEqual(A.public_site_origin(value), '')
        self.assertEqual(A.public_site_origin('https://TALIMKABUTAR.UZ:443/'), 'https://talimkabutar.uz')

    def test_copied_bot_link_and_trimmed_secret_enable_login(self):
        with patch.dict(os.environ, {'KABUTAR_BOT_USERNAME':' https://t.me/my_kabutar_bot/ ',
                'KABUTAR_BOT_AUTH_SECRET':'  ' + 's' * 32 + '\n'}):
            service = A.AuthService(self.p)
        self.assertEqual(service.telegram_config()['bot_username'], 'my_kabutar_bot')
        self.assertTrue(service.telegram_config()['enabled'])
        service.bot_auth('s' * 32)

    def test_bot_username_rejects_unrelated_link_or_query(self):
        for value in ('https://attacker.example/my_bot', 'https://t.me/my_bot?start=payload',
                      'https://person@t.me/my_bot', 'https://t.me/my_bot/other', 'bad bot'):
            self.assertEqual(A.normalize_bot_username(value), '')

    def test_config_diagnostics_never_return_secrets(self):
        self.service.bot_secret = ''
        config = self.app.routes['/auth/config']()['telegram']
        self.assertFalse(config['enabled'])
        self.assertIn('KABUTAR_BOT_AUTH_SECRET', config['reason'])
        self.service.bot_secret = 'only-a-test-secret-' + 'x' * 32
        self.service.bot_username = ''
        config = self.app.routes['/auth/config']()['telegram']
        self.assertIn('KABUTAR_BOT_USERNAME', config['reason'])
        self.assertNotIn(self.service.bot_secret, str(config))

    def test_router_startup_registration_remains_compatible(self):
        app = FakeApp()
        delattr(app, 'router')
        callbacks = []
        app.router = types.SimpleNamespace(add_event_handler=lambda event, fn:callbacks.append((event, fn)))
        app.add_event_handler = None
        service = A.register_auth(app, self.p)
        self.assertEqual(callbacks, [('startup', service.migrate)])

    def imported_phone(self):
        self.db.state['users'][-7] = {'user_id':-7, 'role':'oqituvchi',
            'universitet_id':12, 'full_name':'Imported teacher'}
        self.db.state['phones']['+998901234567'] = -7
        self.db.state['university_invites'].append(-7)

    def test_admin_contact_reservation_does_not_block_real_telegram_login(self):
        self.imported_phone()
        del self.db.state['users'][111]
        self.db.state['google'].clear()
        placeholder = dict(self.db.state['users'][-7])
        self.app.routes['/auth/telegram/confirm'](self.confirm_body(), 's' * 32)
        result = self.app.routes['/auth/telegram/poll'](self.body, self.request)
        self.assertEqual(result['user_id'], 111)
        self.assertEqual(self.p._jwt_tekshir(result['token']), 111)
        self.assertEqual(self.db.state['users'][111]['role'], 'kabutar')
        self.assertNotIn('universitet_id', self.db.state['users'][111])
        self.assertEqual(self.db.state['users'][-7], placeholder)
        self.assertEqual(self.db.state['university_invites'], [-7])
        self.assertEqual(self.db.state['phones']['+998901234567'], 111)
        self.assertEqual(self.db.state['identities'][111]['user_id'], 111)

    def test_negative_google_owner_still_blocks_phone_rebinding(self):
        self.imported_phone()
        self.db.state['google']['existing-owner@example.com'] = -7
        self.assert_http(409, self.app.routes['/auth/telegram/confirm'], self.confirm_body(), 's' * 32)
        self.assertEqual(self.db.state['phones']['+998901234567'], -7)
        self.assertFalse(self.db.state['identities'])

    def test_negative_legacy_phone_without_import_evidence_is_not_reclaimed(self):
        self.imported_phone()
        self.db.state['university_invites'].clear()
        self.assert_http(409, self.app.routes['/auth/telegram/confirm'], self.confirm_body(), 's' * 32)
        self.assertEqual(self.db.state['phones']['+998901234567'], -7)

    def test_password_or_session_owned_negative_profile_is_not_reclaimed(self):
        for kind in ('password', 'session', 'bot_account'):
            with self.subTest(kind=kind):
                self.setUp()
                self.imported_phone()
                if kind == 'password':
                    self.db.state['passwords'][-7] = 'existing-password-hash'
                elif kind == 'session':
                    self.service.issue_session(-7, 'google')
                else:
                    self.db.state['accounts'] = [{'uid':-7,'telegram_id':999,'account_index':0}]
                self.assert_http(409, self.app.routes['/auth/telegram/confirm'], self.confirm_body(), 's' * 32)
                self.assertEqual(self.db.state['phones']['+998901234567'], -7)

    def test_verified_telegram_identity_wins_over_unverified_import_reservation(self):
        self.imported_phone()
        self.db.state['identities'][999] = {'telegram_id':999,'user_id':-7,'phone':'+998901234567'}
        self.assert_http(409, self.app.routes['/auth/telegram/confirm'], self.confirm_body(), 's' * 32)
        self.assertEqual(self.db.state['identities'][999]['user_id'], -7)
        self.assertNotIn(111, self.db.state['identities'])


if __name__ == '__main__':
    unittest.main()
